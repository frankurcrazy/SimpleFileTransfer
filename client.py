#!/usr/bin/env python

import asyncio
import sys
import argparse
import time

from SimpleFileTransfer.client import SimpleFileTransferClient
from SimpleFileTransfer.client import create_task

def main():
    parser = argparse.ArgumentParser( \
        description="Simple File Transfer Client")
    parser.add_argument('--host', metavar="host", \
                        help='Address of Simple File Transfer Server', \
                        type=str, required=True)
    parser.add_argument('--port', metavar="port", \
                        help='Port of Simple File Transfer Server', \
                        type=int, default=9487)
    action_group = parser.add_mutually_exclusive_group(required=True)
    action_group.add_argument('--upload-file', metavar=('src', 'dst'), \
                        help='File to upload', type=str, nargs=2)
    action_group.add_argument('--upload-dir', metavar=('src', 'dst'), \
                        help='Directory to upload', type=str, nargs=2)
    action_group.add_argument('--download-file', metavar=('src', 'dst'), \
                        help='File to download', type=str, nargs=2)
    action_group.add_argument('--download-dir', metavar=('src', 'dst'), \
                        help='Directory to download', type=str, nargs=2)
    action_group.add_argument('--list-dir', metavar='path', \
                        help='Directory to list', type=str, default='/')
    parser.add_argument('--retry', metavar='retry time', type=int, default=3, \
                        help='Times to retry connection before giveup')
    parser.add_argument('--retry-interval', metavar='retry interval', type=int, default=3, \
                        help='Retry interval')
                        
    args = parser.parse_args()
    task = create_task(args)
    
    loop = asyncio.get_event_loop()

    retry = args.retry
    while retry > 0:
        try:
            coro = loop.create_connection(lambda: SimpleFileTransferClient(task), args.host, args.port)
            loop.run_until_complete(coro)
            break
        except Exception as exc:
            retry -= 1
            if retry > 0:
                retry_msg = ", retry in {0} " \
                "seconds.".format(args.retry_interval)
            else:
                retry_msg = "."

            print("{0}{1} ({2}/{3})"\
                    .format(str(exc), retry_msg, \
                            args.retry - retry, args.retry), file=sys.stderr)

            if retry > 0:
                time.sleep(args.retry_interval)

    if retry == 0:
        print("Failed connecting to server.", file=sys.stderr)
    else:
        loop.run_forever()
        loop.close()
    return 0

if __name__ == '__main__':
    sys.exit(main())
