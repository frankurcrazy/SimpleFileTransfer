#!/usr/bin/env python
#-*- coding: utf-8 -*-

import asyncio
import sys
import argparse
import struct
import pickle
import os

from .base import SimpleFileTransferBase
from .handler import SimpleFileTransferServerHandler
from .message import *

class SimpleFileTransferServer(asyncio.Protocol, SimpleFileTransferBase):

    def __init__(self):
        super().__init__()

        self.handler = SimpleFileTransferServerHandler(self)
        
    def message_received(self, msg):
        self.handler.dispatch(msg)
        
    def decode_msgs(self):
        while len(self.rcvbuf) > 4:
            view = memoryview(self.rcvbuf)
            msg_len, = struct.unpack("!I", view[:4])
            
            msg = None
            if len(view[4:]) >= msg_len:
                msg = pickle.loads(view[4:4+msg_len])
                self.message_received(msg)
                
            del view
            if msg: del self.rcvbuf[:4+msg_len]
            else: break
        
    def connection_made(self, transport):
        print("Connection made...")
        self.transport = transport
        
    def data_received(self, data):
        print("Received {0} bytes".format(len(data)))
        self.rcvbuf += data
        self.decode_msgs()
        
    def send_message(self, msg):
        print("Sent: {0}".format(msg))
        raw = pickle.dumps(msg)
        raw = struct.pack("!I", len(raw)) + raw
        self.transport.write(raw)
        print("Sent {0} bytes".format(len(raw)))
        
    def send_error(self, error_msg):
        err = {
            SimpleFileTransferMessageField.ACTION: \
                SimpleFileTransferActionType.ERROR,
            
            SimpleFileTransferMessageField.MSG: \
                error_msg,
        }
        
        self.send_message(err)
    
