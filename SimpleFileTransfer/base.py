#!/usr/bin/env python
#-*- coding: utf-8 -*-

import pickle
import asyncio
import struct
from .message import *

class SimpleFileTransferBase(asyncio.Protocol):
       
    def __init__(self):
        self.rcvbuf = bytearray()
        self.pause = False

    def message_received(self, msg):
        raise NotImplementedError

    def pause_writing(self):
        self.pause = True
    
    def resume_writing(self):
        self.pause = False
    
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

