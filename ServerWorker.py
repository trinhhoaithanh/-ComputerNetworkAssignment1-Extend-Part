from random import randint
import sys, traceback, threading, socket

from VideoStream import VideoStream
from RtpPacket import RtpPacket

class ServerWorker:
	SETUP = 'SETUP'
	PLAY = 'PLAY'
	PAUSE = 'PAUSE'
	TEARDOWN = 'TEARDOWN'
	CHANGESPEED = 'CHANGESPEED'
	DESCRIBE = 'DESCRIBE'
	SWITCHMOVIE = 'SWITCHMOVIE'
	
	INIT = 0
	READY = 1
	PLAYING = 2
	SWITCH = 3
	state = INIT

	OK_200 = 0
	FILE_NOT_FOUND_404 = 1
	CON_ERR_500 = 2
	
	STANDARD_TIME_OF_1_PACKET = 0.05
	clientInfo = {}
	
	def __init__(self, clientInfo):
		self.clientInfo = clientInfo
  
		self.eventCreated = False
		self.timeForEachFrame = self.STANDARD_TIME_OF_1_PACKET
	def run(self):
		threading.Thread(target=self.recvRtspRequest).start()
	
	def recvRtspRequest(self):
		"""Receive RTSP request from the client."""
		connSocket = self.clientInfo['rtspSocket'][0]
		while True:     
			try:
				data = connSocket.recv(256)
			except:
				pass
			if data:
				print("Data received:\n" + data.decode("utf-8"))
				self.processRtspRequest(data.decode("utf-8"))
	
	def processRtspRequest(self, data):
		"""Process RTSP request sent from the client."""
		# Get the request type
		request = data.split('\n')
		line1 = request[0].split(' ')
		self.requestType = line1[0]
		
		# Get the media file name
		filename = line1[1]
		
		# print(request[1].split(' '))
		# Get the RTSP sequence number 
		seq = request[1].split(' ')
		# print('seq ne: ')
		# print(seq)
		# print(seq[1])
		# Process SETUP request
		if self.requestType == self.SETUP:
			if self.state == self.INIT:
				# Update state
				print("processing SETUP\n")
				
				try:
					self.clientInfo['videoStream'] = VideoStream(filename)
					self.state = self.READY
				except IOError:
					self.replyRtsp(self.FILE_NOT_FOUND_404, seq[1])
				
				# Generate a randomized RTSP session ID
				self.clientInfo['session'] = randint(100000, 999999)
				
				# Send RTSP reply
				self.replyRtsp(self.OK_200, seq[1])
				
				# Get the RTP/UDP port from the last line
				self.clientInfo['rtpPort'] = request[2].split(' ')[3]
    
				# Create a new socket for RTP/UDP
				self.clientInfo["rtpSocket"] = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	
		# Process PLAY request 		
		elif self.requestType == self.PLAY:
			if self.state == self.READY:
				print("processing PLAY\n")
				self.state = self.PLAYING
				
				self.replyRtsp(self.OK_200, seq[1])
				
				# Create a new thread and start sending RTP packets
				self.clientInfo['event'] = threading.Event()
				self.clientInfo['worker']= threading.Thread(target=self.sendRtp) 
				self.clientInfo['worker'].start()

				self.eventCreated = True
				# print('clear roi ma')
		# Process PAUSE request
		elif self.requestType == self.PAUSE:
			if self.state == self.PLAYING:
				print("processing PAUSE\n")
				self.state = self.READY
				
				self.clientInfo['event'].set()
			
				self.replyRtsp(self.OK_200, seq[1])
		
		# Process TEARDOWN request
		elif self.requestType == self.TEARDOWN:
			print("processing TEARDOWN\n")
			if(self.eventCreated):
				self.clientInfo['event'].set()
			
			self.replyRtsp(self.OK_200, seq[1])
			self.eventCreated = False
			# Close the RTP socket
			self.clientInfo['rtpSocket'].close()

		# Process CHANGESPEED request
		elif self.requestType == self.CHANGESPEED:
			print("processing CHANGESPEED\n")
			self.timeForEachFrame = self.STANDARD_TIME_OF_1_PACKET / float((request[0].split(' ')[1])[1:])
			self.replyRtsp(self.OK_200, seq[1])
   
		# Process DESCRIBE request
		elif self.requestType == self.DESCRIBE:
			print("processing DESCRIBE\n")
			self.replyRtsp(self.OK_200, seq[1])
		
		# Process SWITCHMOVIE request
		elif self.requestType == self.SWITCHMOVIE:
			print("processing SWITCHMOVIE\n")
			if(self.eventCreated):
				self.clientInfo['event'].set()
			
			self.replyRtsp(self.OK_200, seq[1])
			self.eventCreated = False
			# Close the RTP socket
			self.clientInfo['rtpSocket'].close()
		else:
			return
	def sendRtp(self):
		"""Send RTP packets over UDP."""
		while True:
			self.clientInfo['event'].wait(self.timeForEachFrame) 
			
			# Stop sending if request is PAUSE or TEARDOWN
			if self.clientInfo['event'].isSet(): 
				# print('check set event')
				break 
				
			data = self.clientInfo['videoStream'].nextFrame()
			if data: 
				frameNumber = self.clientInfo['videoStream'].frameNbr()
				try:
					address = self.clientInfo['rtspSocket'][1][0]
					port = int(self.clientInfo['rtpPort'])
					# print("rtp send: " + address + " " + str(port))
					self.clientInfo['rtpSocket'].sendto(self.makeRtp(data, frameNumber),(address,port))
					
				except:
					print("Connection Error")
					#print('-'*60)
					#traceback.print_exc(file=sys.stdout)
					#print('-'*60)

	def makeRtp(self, payload, frameNbr):
		"""RTP-packetize the video data."""
		version = 2
		padding = 0
		extension = 0
		cc = 0
		marker = 0
		pt = 26 # MJPEG type
		seqnum = frameNbr
		ssrc = 0 
		
		rtpPacket = RtpPacket()
		
		rtpPacket.encode(version, padding, extension, cc, seqnum, marker, pt, ssrc, payload)
		
		return rtpPacket.getPacket()
		
	def replyRtsp(self, code, seq):
		"""Send RTSP reply to the client."""
		if code == self.OK_200:
			#print("200 OK")
			reply = 'RTSP/1.0 200 OK\nCSeq: ' + seq + '\nSession: ' + str(self.clientInfo['session'])
			if self.requestType == self.SETUP:
				reply += '\nThe number of frame of video: ' + str(self.clientInfo['videoStream'].numFrameVideo)
				reply += '\nStandard time between frams: ' + str(self.STANDARD_TIME_OF_1_PACKET)
			elif self.requestType == self.DESCRIBE:
				reply += '\nv=0' 
				reply += '\no=- ' + str(self.clientInfo['session']) + ' - IN ' + 'IP4 ' + str(self.clientInfo['rtspSocket'][1][0])
				reply += '\ns=RTSP session'
				reply += '\nm=video ' + str(self.clientInfo['rtpPort']) + ' RTP/AVP 26' #26: Size of payload type field
				reply += '\na=rtpmap:26 JPEG/90000' 
				reply += '\na=charset:utf-8'
				reply += '\na=control:streamid=' + str(self.clientInfo['session'])
				reply += '\na=control:' + self.clientInfo['videoStream'].filename
			connSocket = self.clientInfo['rtspSocket'][0]
			connSocket.send(reply.encode())
		# Error messages
		elif code == self.FILE_NOT_FOUND_404:
			print("404 NOT FOUND")
		elif code == self.CON_ERR_500:
			print("500 CONNECTION ERROR")
