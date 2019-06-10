#!/usr/bin/env python

import os
import sys
import time
import asyncio
from typing import cast, List

import asyncssh
import requests
import structlog


log = structlog.PrintLogger() # pylint: disable=invalid-name


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
    resp = requests.get('http://metadata.google.internal/computeMetadata/v1/instance/hostname')
    resp.raise_for_status()
    return Hostname(resp.text)


def get_instance_names() -> List[str]:
    return os.environ['NODES'].split()


async def start_rnode_on(instance_hostname: Hostname) -> str:
    command = 'docker pull rchain'
    async with asyncssh.connect(str(instance_hostname)) as conn:
        log.info("{}: {}".format(instance_hostname, command))
        result = await conn.run(command, check=True)
        log.info("{}: {}".format(instance_hostname, result))
        return cast(str, result)


async def set_up_network() -> None:
    this_hostname = get_google_cloud_hostname()
    for instance_name in get_instance_names():
        instance_hostname = this_hostname.with_instance_name(instance_name)
        await start_rnode_on(instance_hostname)


async def deploy_propose_forever() -> None:
    log.info("Going to sleep...")
    while True:
        time.sleep(1)


async def main() -> int:
    try:
        await set_up_network()
        await deploy_propose_forever()
    except Exception: # pylint: disable=broad-except
        log.exception("Failure")
        return 1
    return 0


if __name__ == '__main__':
    # pylint: disable=invalid-name
    event_loop = asyncio.get_event_loop()
    exit_code = event_loop.run_until_complete(main())
    sys.exit(exit_code)
