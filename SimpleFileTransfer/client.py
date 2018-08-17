#!/usr/bin/env python

import asyncio
import sys
import argparse
import struct
import pickle
import stat
import os

from .message import *
from .handler import SimpleFileTransferClientHandler
from .handler import SimpleFileTransferClientMessageHandler as cMsgHandler
from .base import SimpleFileTransferBase

class SimpleFileTransferClient(asyncio.Protocol, SimpleFileTransferBase):
    def __init__(self, task):
        super().__init__()

        self.handler = SimpleFileTransferClientHandler(self)
        self.msg_handler = cMsgHandler(self)
        self.task = task
        
    def pause_writing(self):
        self.pause = True
    
    def resume_writing(self):
        self.pause = False
    
    def message_received(self, msg):
        self.msg_handler.dispatch(msg)

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
        self.transport = transport
        self.handler.dispatch(self.task)
        
    def data_received(self, data):
        self.rcvbuf += data
        self.decode_msgs()
        
    def send_message(self, msg):
        raw = pickle.dumps(msg)
        raw = struct.pack("!I", len(raw)) + raw
        self.transport.write(raw)
        
    def send_error(self, error_msg):
        err = {
            SimpleFileTransferMessageField.ACTION: \
                SimpleFileTransferActionType.ERROR,
            
            SimpleFileTransferMessageField.MSG: \
                error_msg,
        }
        
        self.send_message(err)

    def connection_lost(self, ex):
        loop = asyncio.get_event_loop()
        loop.stop()

def create_task(args):
    task = dict()
    
    if args.download_file:
        task.update({
            SimpleFileTransferMessageField.ACTION: \
                SimpleFileTransferActionType.DOWNLOAD_FILE,
                
            SimpleFileTransferMessageField.SRC: args.download_file[0],
            SimpleFileTransferMessageField.DST: args.download_file[1]
        })
    
    elif args.download_dir:
        task.update({
            SimpleFileTransferMessageField.ACTION: \
                SimpleFileTransferActionType.DOWNLOAD_DIR,
            SimpleFileTransferMessageField.SRC: args.download_dir[0],
            SimpleFileTransferMessageField.DST: args.download_dir[1]
        })
        
    elif args.upload_file:
        task.update({
            SimpleFileTransferMessageField.ACTION: \
                SimpleFileTransferActionType.UPLOAD_FILE,
            SimpleFileTransferMessageField.SRC: args.upload_file[0],
            SimpleFileTransferMessageField.DST: args.upload_file[1]
        })
        
    elif args.upload_dir:
        task.update({
            SimpleFileTransferMessageField.ACTION: \
                SimpleFileTransferActionType.UPLOAD_DIR,
            SimpleFileTransferMessageField.SRC: args.upload_dir[0],
            SimpleFileTransferMessageField.DST: args.upload_dir[1]
        })
        
    elif args.list_dir:
        task.update({
            SimpleFileTransferMessageField.ACTION: \
                SimpleFileTransferActionType.LIST_DIR,
            SimpleFileTransferMessageField.PATH: args.list_dir,
        })
        
    return task
    
