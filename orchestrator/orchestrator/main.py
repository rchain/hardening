#!/usr/bin/env python

import os
import sys
import time
import asyncio
import logging
from typing import (
    List,
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


async def start_rnode_on(ssh_private_key_file_path: str, instance_hostname: Hostname) -> None:
    command = 'docker pull rchain/rnode:latest'
    async with asyncssh.connect(str(instance_hostname), client_keys=[ssh_private_key_file_path], known_hosts=None) as conn:
        await conn.run(command, check=True)


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
