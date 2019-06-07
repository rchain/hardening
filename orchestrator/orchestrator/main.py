#!/usr/bin/env python

import os
import sys
import time
import asyncio
from typing import List

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


def get_google_cloud_hostname() -> Hostname:
    resp = requests.get('http://metadata.google.internal/computeMetadata/v1/instance/hostname')
    resp.raise_for_status()
    return Hostname(resp.text)


def get_nodes() -> List[str]:
    return os.environ['NODES'].split()


async def main() -> int:
    log.info("Got nodes: {}".format(get_nodes()))
    log.info("Going to sleep...")
    while True:
        time.sleep(1)
    return 0


if __name__ == '__main__':
    # pylint: disable=invalid-name
    event_loop = asyncio.get_event_loop()
    exit_code = event_loop.run_until_complete(main())
    sys.exit(exit_code)
