#!/usr/bin/env python
#-*- coding: utf-8 -*-

import stat
import sys
import os
import asyncio
from .message import SimpleFileTransferActionType as Action
from .message import SimpleFileTransferMessageField as Field

class SimpleFileTransferClientMessageHandler:

    def __init__(self, proto):
        self.proto = proto
        self.loop = asyncio.get_event_loop()

        self.handler_map = {
            Action.LIST_DIR: self.list_dir,
            Action.ERROR: self.error_msg,
            Action.TASK_DONE: self.task_done,
        }

    def dispatch(self, msg):
        action = msg[Field.ACTION]

        # Schedule a task to the loop
        self.loop.create_task( \
                self.handler_map[action](msg))

    async def list_dir(self, msg):
        path = msg[Field.PATH]
        files = msg[Field.DATA]

        print("Listing of directory \"{0}\":".format(path))
        for file in files:
            stat_string = "{mod:10s}\t{uid:5d}\t{gid:5d}\t{size:10d}".format( \
                mod = stat.filemode(files[file].st_mode),
                uid = files[file].st_uid,
                gid = files[file].st_gid,
                size = files[file].st_size)
                
            print("{0}\t{1}".format(stat_string, file))

        return True

    async def error_msg(self, msg):
        err_msg = msg[Field.MSG]
        print(err_msg, file=sys.stderr)
        return True

    async def task_done(self, msg):
        self.proto.connection_lost(None) 

class SimpleFileTransferServerHandler:

    def __init__(self, proto):
        self.proto = proto
        
        self.handler = {
            Action.DOWNLOAD_FILE: self.download,
            Action.DOWNLOAD_DIR: self.download_dir,
            Action.UPLOAD_FILE: self.upload,
            Action.UPLOAD_DIR: self.upload_dir,
            Action.LIST_DIR: self.list_dir,
            Action.FILE_INFO: None,
        }
    
    def dispatch(self, msg):
        """ Dispatch the task 
        """
        
        loop = asyncio.get_event_loop() 
        loop.create_task( \
            self.handler[msg[Field.ACTION]](msg))

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
            path = msg[Field.PATH]
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
            Field.ACTION: \
                Action.LIST_DIR,
            Field.PATH: \
                msg[Field.PATH],
            Field.DATA: \
                dir_dict
        }
        
        self.proto.send_message(msg)
        self.task_done()
        return True

    async def remove(self, msg):
        path = msg[Field.PATH]

        if not os.path.exists(path):
            self.proto.send_error("File does not exist.") 
            return False

        elif not os.path.isfile(path):
            self.proto.send_error("Target is not a file.")
            return False
            
        else:
            try:
                os.remove(path)
            except Exception as exc:
                self.proto.send_error(str(exc))
                return False

            return True


    def task_done(self):
        msg = {
            Field.ACTION: \
                Action.TASK_DONE
        }

        self.proto.send_message(msg)
        return True

class SimpleFileTransferClientHandler:

    def __init__(self, proto):
        self.proto = proto
        
        self.handler = {
            Action.DOWNLOAD_FILE: self.download,
            Action.DOWNLOAD_DIR: self.download_dir,
            Action.UPLOAD_FILE: self.upload,
            Action.UPLOAD_DIR: self.upload_dir,
            Action.LIST_DIR: self.list_dir,
            Action.FILE_INFO: None,
        }
    
    def dispatch(self, task):
        """ Dispatch the task 
        """
        
        loop = asyncio.get_event_loop() 
        loop.create_task( \
            self.handler[task[Field.ACTION]](task))

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
            Field.ACTION: Action.LIST_DIR,
            Field.PATH: task[Field.PATH],
        }
        
        self.proto.send_message(msg)
        return True

