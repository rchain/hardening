#!/usr/bin/env python

import os
import sys
import shlex
import asyncio
import logging
from typing import (
    cast,
    List,
    Dict,
    Any,
)

import asyncssh
import requests


RNODE_DOCKER_IMAGE = 'rchain/rnode:v0.9.7'


class OrchestratorException(Exception):
    pass


class BootstrapStartFailedError(OrchestratorException):
    pass


class PeersNumberNotReachedError(OrchestratorException):
    pass


class Hostname:
    def __init__(self, hostname: str) -> None:
        self.instance_name, self.domain = hostname.split('.', maxsplit=1)

    def get_instance_name(self) -> str:
        return self.instance_name

    def get_domain(self) -> str:
        return self.domain

    def with_instance_name(self, network_prefix: str, new_instance_name: str) -> 'Hostname':
        return Hostname('{}-{}.{}'.format(network_prefix, new_instance_name, self.domain))

    def __str__(self) -> str:
        return '{}.{}'.format(self.instance_name, self.domain)


def get_google_cloud_hostname() -> Hostname:
    headers = {
        'Metadata-Flavor': 'Google',
    }
    resp = requests.get('http://metadata.google.internal/computeMetadata/v1/instance/hostname', headers=headers)
    resp.raise_for_status()
    return Hostname(resp.text)


def get_instance_names() -> List[str]:
    return os.environ['NODES'].split()


def render_command(fields: List[str]) -> str:
    return ' '.join(shlex.quote(f) for f in fields)


def make_rnode_command() -> List[str]:
    shell_fields = [
        'docker',
        'run',
        '--detach',
        '--name=rnode',
        '--network=host',
        '--volume=/var/lib/rnode:/var/lib/rnode',
        '--volume=/var/lib/rnode-static:/var/lib/rnode-static:ro',
        '--entrypoint=/opt/docker/bin/rnode',
        RNODE_DOCKER_IMAGE,
        '--grpc-port=40401',
        '-J-Xdebug',
        '-J-Xrunjdwp:transport=dt_socket,address=127.0.0.1:8888,server=y,suspend=n',
        '-XX:+HeapDumpOnOutOfMemoryError',
        '-XX:HeapDumpPath=/root/heapdump_OOM.hprof',
        '-XX:+ExitOnOutOfMemoryError',
        '-XX:ErrorFile=/root/hs_err.log',
        '-XX:MaxJavaStackTraceDepth=100000',
        '-XX:NativeMemoryTracking=detail',
        '-Dlogback.configurationFile=/var/lib/rnode-static/logback.xml',
        '--profile=docker',
        '--config-file=/var/lib/rnode-static/rnode.conf',
        'run',
        '--network=hardnet1',
        '--map-size=1099511627776',
        '--kademlia-port=40404',
        '--port=40400',
        '--required-sigs=0',
        '--store-type=v2',
    ]
    return shell_fields


def make_rnode_bootstrap_command() -> List[str]:
    shell_fields = make_rnode_command()
    shell_fields.append('--standalone')
    return shell_fields


def make_rnode_peer_command(bootstrap_uri: str) -> List[str]:
    shell_fields = make_rnode_command()
    shell_fields.append('--bootstrap={}'.format(bootstrap_uri))
    return shell_fields


async def start_peer_node(conn: Any, bootstrap_uri: str) -> None:
    docker_pull = ['docker', 'pull', RNODE_DOCKER_IMAGE]
    rnode_command = make_rnode_peer_command(bootstrap_uri)
    await conn.run(render_command(docker_pull), check=True)
    await conn.run(render_command(['docker', 'kill', 'rnode']))
    await conn.run(render_command(['docker', 'rm', 'rnode']))
    await conn.run(render_command(rnode_command), check=True)


def get_rnode_status(hostname: Hostname) -> Dict[str, str]:
    status_url = 'http://{}:40403/status'.format(hostname)
    resp = requests.get(status_url)
    resp.raise_for_status()
    return cast(Dict[str, str], resp.json())


async def wait_bootstrap_started(bootstrap_hostname: Hostname) -> str:
    for _ in range(10 * 60):
        try:
            status = get_rnode_status(bootstrap_hostname)
            return status['address']
        except requests.exceptions.ConnectionError:
            pass
        await asyncio.sleep(1)
    raise BootstrapStartFailedError()


async def start_bootstrap_node(bootstrap_conn: Any) -> None:
    docker_pull = ['docker', 'pull', RNODE_DOCKER_IMAGE]
    rnode_command = make_rnode_bootstrap_command()
    await bootstrap_conn.run(render_command(docker_pull), check=True)
    await bootstrap_conn.run(render_command(['docker', 'kill', 'rnode']))
    await bootstrap_conn.run(render_command(['docker', 'rm', 'rnode']))
    await bootstrap_conn.run(render_command(rnode_command), check=True)


async def wait_peers_connected(bootstrap_hostname: Hostname, desired_peers_number: int) -> None:
    for _ in range(10 * 60):
        try:
            status = get_rnode_status(bootstrap_hostname)
            peers = int(status['peers'])
            logging.info("Current number of peers connected to bootstrap: %d", peers)
            if peers >= desired_peers_number:
                return
        except requests.exceptions.ConnectionError:
            pass
        await asyncio.sleep(5)
    raise PeersNumberNotReachedError(desired_peers_number)


async def set_up_network() -> None:
    network = os.environ['NETWORK']
    ssh_private_key_file_path = os.environ['SSH_PRIVATE_KEY_FILE_PATH']
    this_hostname = get_google_cloud_hostname()
    bootstrap_hostname = this_hostname.with_instance_name(network, 'bootstrap')
    async with asyncssh.connect(str(bootstrap_hostname), client_keys=[ssh_private_key_file_path], known_hosts=None) as bootstrap_conn:
        await start_bootstrap_node(bootstrap_conn)
        bootstrap_uri = await wait_bootstrap_started(bootstrap_hostname)
        for instance_name in get_instance_names():
            instance_hostname = this_hostname.with_instance_name(network, instance_name)
            async with asyncssh.connect(str(instance_hostname), client_keys=[ssh_private_key_file_path], known_hosts=None) as peer_conn:
                await start_peer_node(peer_conn, bootstrap_uri)

    desired_peers_number = len(get_instance_names())
    await wait_peers_connected(bootstrap_hostname, desired_peers_number)


async def deploy_propose_forever() -> None:
    logging.info("Going to sleep...")
    while True:
        await asyncio.sleep(1)


async def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    try:
        await set_up_network()
        await deploy_propose_forever()
    except asyncssh.process.ProcessError as process_error:
        logging.exception(process_error)
        logging.error("returncode: %d", process_error.returncode)
        logging.error("stdout: %s", process_error.stdout)
        logging.error("stderr: %s", process_error.stderr)
    except Exception: # pylint: disable=broad-except
        logging.exception("Failure")
        return 1
    return 0


if __name__ == '__main__':
    # pylint: disable=invalid-name
    event_loop = asyncio.get_event_loop()
    exit_code = event_loop.run_until_complete(main())
    sys.exit(exit_code)
