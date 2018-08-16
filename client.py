#!/usr/bin/env python

import asyncio
import sys
import argparse

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
                        
    args = parser.parse_args()
    task = create_task(args)
    
    loop = asyncio.get_event_loop()
    coro = loop.create_connection(lambda: SimpleFileTransferClient(task), args.host, args.port)
    loop.run_until_complete(coro)
    loop.run_forever()
    loop.close()
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
