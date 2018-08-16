#!/usr/bin/env python
#-*- coding: utf-8 -*-

import asyncio
import sys
import argparse
from SimpleFileTransfer.server import SimpleFileTransferServer

def main():

    parser = argparse.ArgumentParser( \
        description="Simple File Transfer Client")
    parser.add_argument('--host', metavar="host", \
                        help='Address of Simple File Transfer Server', \
                        type=str, default="0.0.0.0")
    parser.add_argument('--port', metavar="port", \
                        help='Port of Simple File Transfer Server', \
                        type=int, default=9487)
                        
    args = parser.parse_args()
    
    loop = asyncio.get_event_loop()
    
    print("[+] Server listening on {0}:{1}.".format(args.host, args.port))
    coro = loop.create_server(SimpleFileTransferServer, \
                host=args.host, port=args.port)
    loop.run_until_complete(coro)
    loop.run_forever()
    loop.close()
    
    return 0

if __name__ == '__main__':
    sys.exit(main())

