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

class SimpleFileTransferServer(SimpleFileTransferBase):

    def __init__(self):
        super().__init__()

        self.handler = SimpleFileTransferServerHandler(self)
        
    def message_received(self, msg):
        self.handler.dispatch(msg)
        
    def connection_made(self, transport):
        print("Connection made...")
        self.transport = transport

