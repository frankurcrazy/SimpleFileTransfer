#!/usr/bin/env python
#-*- coding: utf-8 -*-

import os
import asyncio
from .message import *

class SimpleFileTransferServerHandler:

    def __init__(self, proto):
        self.proto = proto
        
        self.handler = {
            SimpleFileTransferActionType.DOWNLOAD_FILE: self.download,
            SimpleFileTransferActionType.DOWNLOAD_DIR: self.download_dir,
            SimpleFileTransferActionType.UPLOAD_FILE: self.upload,
            SimpleFileTransferActionType.UPLOAD_DIR: self.upload_dir,
            SimpleFileTransferActionType.LIST_DIR: self.list_dir,
            SimpleFileTransferActionType.FILE_INFO: None,
        }
    
    def dispatch(self, msg):
        """ Dispatch the task 
        """
        
        loop = asyncio.get_event_loop() 
        loop.create_task( \
            self.handler[msg[SimpleFileTransferMessageField.ACTION]](msg))

    async def download(self, msg):
        raise NotImplementedError
        
    async def upload(self, msg):
        raise NotImplementedError
        
    async def download_dir(self, msg):
        raise NotImplementedError
    
    async def upload_dir(self, msg):
        raise NotImplementedError
        
    async def list_dir(self, msg):
        try:
            path = msg[SimpleFileTransferMessageField.PATH]
            dir_list = os.listdir(path)
        except Exception as e:
            self.proto.send_error(str(e))
            self.task_done()
            return False

        dir_dict = dict()

        for dir_ in dir_list:
            dir_dict.update({
                dir_: os.lstat(os.path.join(path, dir_))
            })
        
        msg = {
            SimpleFileTransferMessageField.ACTION: \
                SimpleFileTransferActionType.LIST_DIR,
            SimpleFileTransferMessageField.PATH: \
                msg[SimpleFileTransferMessageField.PATH],
            SimpleFileTransferMessageField.DATA: \
                dir_dict
        }
        
        self.proto.send_message(msg)
        self.task_done()
        return True

    def task_done(self):
        msg = {
            SimpleFileTransferMessageField.ACTION: \
                SimpleFileTransferActionType.TASK_DONE
        }

        self.proto.send_message(msg)
        return True

class SimpleFileTransferClientHandler:

    def __init__(self, proto):
        self.proto = proto
        
        self.handler = {
            SimpleFileTransferActionType.DOWNLOAD_FILE: self.download,
            SimpleFileTransferActionType.DOWNLOAD_DIR: self.download_dir,
            SimpleFileTransferActionType.UPLOAD_FILE: self.upload,
            SimpleFileTransferActionType.UPLOAD_DIR: self.upload_dir,
            SimpleFileTransferActionType.LIST_DIR: self.list_dir,
            SimpleFileTransferActionType.FILE_INFO: None,
        }
    
    def dispatch(self, task):
        """ Dispatch the task 
        """
        
        loop = asyncio.get_event_loop() 
        loop.create_task( \
            self.handler[task[SimpleFileTransferMessageField.ACTION]](task))

    async def download(self, task):
        raise NotImplementedError
        
    async def upload(self, task):
        raise NotImplementedError
        
    async def download_dir(self, task):
        raise NotImplementedError
    
    async def upload_dir(self, task):
        raise NotImplementedError
        
    async def list_dir(self, task):
        msg = {
            SimpleFileTransferMessageField.ACTION: \
                SimpleFileTransferActionType.LIST_DIR,
            SimpleFileTransferMessageField.PATH: \
                task[SimpleFileTransferMessageField.PATH],
        }
        
        self.proto.send_message(msg)
        return True

