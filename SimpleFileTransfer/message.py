#!/usr/bin/env python
#-*- coding: utf-8 -*-

class SimpleFileTransferMessageField:
    ACTION = 1 << 0
    DATA = 1 << 1
    MSG = 1 << 2
    SRC = 1 << 3
    DST = 1 << 4
    STAT = 1 << 5
    PATH = 1 << 6
    SID = 1 << 7

class SimpleFileTransferActionType:
    DOWNLOAD_FILE = 1 << 0
    UPLOAD_FILE = 1 << 1
    DOWNLOAD_DIR = 1 << 2
    UPLOAD_DIR = 1 << 3
    CHUNK = 1 << 4
    FILE_INFO = 1 << 5
    LIST_DIR = 1 << 6
    ERROR = 1 << 7
    TASK_DONE = 1 << 8
    
