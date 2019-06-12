#!/usr/bin/env python

import os
import sys
import time
import shlex
import asyncio
import logging
from typing import (
    cast,
    List,
    Dict,
)

import asyncssh
import requests


class Hostname:
    def __init__(self, hostname: str) -> None:
        self.instance_name, self.domain = hostname.split('.', maxsplit=1)

    def get_instance_name(self) -> str:
        return self.instance_name

    def get_domain(self) -> str:
        return self.domain

    def with_instance_name(self, new_instance_name: str) -> 'Hostname':
        return Hostname('{}.{}'.format(new_instance_name, self.domain))

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


def make_rnode_command(rnode_docker_image: str) -> List[str]:
    shell_fields = [
        'docker',
        'run',
        '--detach',
        '--name=rnode',
        '--network=host',
        '--env-file=/var/lib/rnode-static/environment.docker',
        '--volume=/var/lib/rnode:/var/lib/rnode',
        '--volume=/var/lib/rnode-static:/var/lib/rnode-static:ro',
        '--volume=/usr/lib/x86_64-linux-gnu/libjemalloc.so.2:/opt/libjemalloc.so.2:ro',
        '--entrypoint=/opt/docker/bin/rnode',
        rnode_docker_image,
        '--grpc-port=40401',
        '-J-Xdebug',
        '-J-Xrunjdwp:transport=dt_socket,address=127.0.0.1:8888,server=y,suspend=n',
        '-XX:+HeapDumpOnOutOfMemoryError',
        '-XX:HeapDumpPath=$DIAG_DIR/heapdump_OOM.hprof',
        '-XX:+ExitOnOutOfMemoryError',
        '-XX:ErrorFile=$DIAG_DIR/hs_err.log',
        '-XX:MaxJavaStackTraceDepth=100000',
        '-XX:NativeMemoryTracking=detail',
        '-Dlogback.configurationFile=/var/lib/rnode-static/logback.xml',
        '-p docker',
        '-c /var/lib/rnode-static/rnode.conf',
        'run',
        '--network=hardnet1',
        '--map-size=1099511627776'
        '--store-type=v2',
        '--genesis-validator=false',
        '--kademlia-port=40404',
        '--port=40400',
        '--required-sigs=0',
    ]
    return shell_fields


def make_rnode_bootstrap_command(rnode_docker_image: str) -> List[str]:
    shell_fields = make_rnode_command(rnode_docker_image)
    shell_fields.append('--standalone=true')
    return shell_fields


def make_rnode_peer_command(rnode_docker_image: str, bootstrap_uri: str) -> List[str]:
    shell_fields = make_rnode_command(rnode_docker_image)
    shell_fields.append('--bootstrap={}'.format(bootstrap_uri))
    return shell_fields


async def start_rnode_on(ssh_private_key_file_path: str, instance_hostname: Hostname) -> None:
    rnode_docker_image = 'rchain/rnode:v0.9.3'
    docker_pull = ['docker', 'pull', rnode_docker_image]
    bootstrap_command = make_rnode_bootstrap_command(rnode_docker_image)
    async with asyncssh.connect(str(instance_hostname), client_keys=[ssh_private_key_file_path], known_hosts=None) as conn:
        await conn.run(render_command(docker_pull), check=True)
        await conn.run(render_command(bootstrap_command), check=True)


async def get_rnode_status(hostname: Hostname) -> Dict[str, str]:
    status_url = 'http://{}/status'.format(hostname)
    resp = requests.get(status_url)
    resp.raise_for_status()
    return cast(Dict[str, str], resp.json())


async def set_up_network() -> None:
    ssh_private_key_file_path = os.environ['SSH_PRIVATE_KEY_FILE_PATH']
    this_hostname = get_google_cloud_hostname()
    for instance_name in get_instance_names():
        instance_hostname = this_hostname.with_instance_name(instance_name)
        await start_rnode_on(ssh_private_key_file_path, instance_hostname)


async def deploy_propose_forever() -> None:
    logging.info("Going to sleep...")
    while True:
        time.sleep(1)


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
