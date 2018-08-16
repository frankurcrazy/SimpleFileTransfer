#!/usr/bin/env python
#-*- coding: utf-8 -*-

import asyncio
import sys
import argparse
import struct
import pickle
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

class SimpleFileTransferServer(asyncio.Protocol):

	def __init__(self):
		self.rcvbuf = bytearray()
		self.pause = False
		self.handler = SimpleFileTransferServerHandler(self)
		
	def pause_writing(self):
		print("Pause")
		self.pause = True
	
	def resume_writing(self):
		print("Unpause")
		self.pause = False
	
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

