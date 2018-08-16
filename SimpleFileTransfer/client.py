#!/usr/bin/env python

import asyncio
import sys
import argparse
import struct
import pickle
import stat
import os

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

class SimpleFileTransferClient(asyncio.Protocol):
	def __init__(self, task):
		self.rcvbuf = bytearray()
		self.pause = False
		self.handler = SimpleFileTransferClientHandler(self)
		self.task = task
		
	def pause_writing(self):
		self.pause = True
	
	def resume_writing(self):
		self.pause = False
	
	def message_received(self, msg):
		action = msg[SimpleFileTransferMessageField.ACTION] 

		if action == SimpleFileTransferActionType.TASK_DONE:
			self.connection_lost(None)

		if action == SimpleFileTransferActionType.LIST_DIR:
			path = msg[SimpleFileTransferMessageField.PATH]
			files = msg[SimpleFileTransferMessageField.DATA]

			print("Listing of {0}:".format(path))
			for file in files:
				stat_string = "{mod:10s}\t{uid:5d}\t{gid:5d}\t{size:10d}".format( \
					mod = stat.filemode(files[file].st_mode),
					uid = files[file].st_uid,
					gid = files[file].st_gid,
					size = files[file].st_size)
					
				print("{0}\t{1}".format(stat_string, file))

		if action == SimpleFileTransferActionType.ERROR:
			print(msg[SimpleFileTransferMessageField.MSG])

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
