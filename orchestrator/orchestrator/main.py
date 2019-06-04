#!/usr/bin/env python

import sys
import time


def main():
    print("Going to sleep...", file=sys.stderr)
    while True:
        time.sleep(1)
    return 0


if __name__ == '__main__':
    sys.exit(main())
