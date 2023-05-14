from tkinter import *
import tkinter.messagebox
from tkinter import messagebox 
from PIL import Image, ImageTk
import socket, threading, sys, traceback, os
import time
from decimal import Decimal

from RtpPacket import RtpPacket
CACHE_FILE_NAME = "cache-"
CACHE_FILE_EXT = ".jpg"

class Client:
	INIT = 0
	READY = 1
	PLAYING = 2
	SWITCH = 3
	state = INIT
	
	SETUP = 0
	PLAY = 1
	PAUSE = 2
	TEARDOWN = 3
	CHANGESPEED = 4
	DESCRIBE = 5
	SWITCHMOVIE = 6
 	
	# Initiation..
	def __init__(self, master, serveraddr, serverport, rtpport, filename):
		self.master = master
		self.master.protocol("WM_DELETE_WINDOW", self.handler)
		self.createWidgets()
		self.serverAddr = serveraddr
		self.serverPort = int(serverport)
		self.rtpPort = int(rtpport)
		self.fileName = filename
		self.rtspSeq = 0
		self.sessionId = 0
		self.requestSent = -1
		self.teardownAcked = 0
		self.connectToServer()
		self.frameNbr = 0
  
		self.filmIndex = 0
		self.rtpPortOpen = False
		self.numFrameVideo = 0
		self.standardTimeForEachFrame = 0
		self.timeForEachFrame = 0
		self.timeVideoPlayed = 0
		self.lengthOfVideo = 0
		self.standardTimeMultiplyWith = 1
		self.describeYet = False
	# THIS GUI IS JUST FOR REFERENCE ONLY, STUDENTS HAVE TO CREATE THEIR OWN GUI 	
	def createWidgets(self):
		"""Build GUI."""
		# Create Describe button
		self.describeImage = ImageTk.PhotoImage(image=Image.open('describe-button.png').resize((150, 150), Image.ANTIALIAS))
		self.setup = Button(self.master, image=self.describeImage, activebackground="grey", relief=RAISED, bd=5)
		self.setup["text"] = "Describe"
		self.setup["command"] = self.describe
		self.setup.grid(row=5, column=0)
		
		# Create Play button
		self.playImage = ImageTk.PhotoImage(image=Image.open('play-button.png').resize((150, 150), Image.ANTIALIAS))
		self.start = Button(self.master, image=self.playImage, activebackground="grey", relief=RAISED, bd=5)
		self.start["text"] = "Play"
		self.start["command"] = self.playMovie
		self.start.grid(row=5, column=1)

		# Create Pause button
		self.pauseImage = ImageTk.PhotoImage(image=Image.open('pause-button.png').resize((150, 150), Image.ANTIALIAS))
		self.pause = Button(self.master, image=self.pauseImage, activebackground="grey", relief=RAISED, bd=5)
		self.pause["text"] = "Pause"
		self.pause["command"] = self.pauseMovie
		self.pause.grid(row=5, column=2)

		# Create Stop button
		self.stopImage = ImageTk.PhotoImage(image=Image.open('stop-button.png').resize((150, 150), Image.ANTIALIAS))
		self.teardown = Button(self.master, image=self.stopImage, activebackground="grey", relief=RAISED, bd=5)
		self.teardown["text"] = "Stop"
		self.teardown["command"] = self.exitClient
		self.teardown.grid(row=5, column=3)
  
		# Create a label to display current time/total time of video
		self.currAndTotalTime = Label(self.master, text='--:--/--:--', height=2, bd=1, relief=GROOVE, anchor=W)
		self.currAndTotalTime.grid(row=2, column=0, columnspan=2, sticky=W+E+N+S, padx=1, pady=1)
  
		# Create Switch movie button
		self.switch = Button(self.master, text='Watch new movie', height=2, width=21, bd=1, relief=RAISED, bg="black", fg="white", activebackground="grey")
		self.switch["command"] = self.switchMovie
		self.switch.grid(row=2, column=2, columnspan=2, sticky=W+E+N+S, padx=1, pady=1)
		
		# Create ChangeSpeed buttons
		self.x2speed = Button(self.master, text='x2', height=2, width=21, bd=1, relief=RAISED, bg="grey", fg="red", activebackground="red")
		self.x2speed["command"] = lambda: self.changeSpeed(2)
		self.x2speed.grid(row=3, column=3, columnspan=1, pady=1)
  
		self.x1_5speed = Button(self.master, text='x1.5', height=2, width=21, bd=1, relief=RAISED, bg="grey", fg="orange", activebackground="orange")
		self.x1_5speed["command"] = lambda: self.changeSpeed(1.5)
		self.x1_5speed.grid(row=3, column=2, columnspan=1, pady=1)
  
		self.x1speed = Button(self.master, text='x1', height=2, width=21, bd=1, relief=RAISED, bg="grey", fg="yellow", activebackground="yellow")
		self.x1speed["command"] = lambda: self.changeSpeed(1)
		self.x1speed.grid(row=3, column=1, columnspan=1, pady=1)
  
		self.x0_5speed = Button(self.master, text='x0.5', height=2, width=21, bd=1, relief=RAISED, bg="grey", fg="lime", activebackground="lime")
		self.x0_5speed["command"] = lambda: self.changeSpeed(0.5)
		self.x0_5speed.grid(row=3, column=0, columnspan=1, pady=1)
  
		# Create a label to display the packet loss rate
		self.lossRateDisplay = Label(self.master, text='Packet loss rate: - %', height=2, bd=1, relief=GROOVE, anchor=W)
		self.lossRateDisplay.grid(row=4, column=0, columnspan=2, sticky=W+E+N+S, padx=1, pady=1)

		# Create a label to display the data rate
		self.dataRateDisplay = Label(self.master, text='Data rate: - KB/s', height=1, bd=1, relief=GROOVE, anchor=W)
		self.dataRateDisplay.grid(row=4, column=2, columnspan=2, sticky=W+E+N+S, padx=1, pady=1)
  
		# Create a label to display the movie
		self.label = Label(self.master, height=19)
		self.label.grid(row=0, column=0, columnspan=4, sticky=W+E+N+S, padx=5, pady=5) 
  
		# Create a label to display session description file
		self.description = Label(self.master, height=15, relief=GROOVE, text='----SESSION DESCRIPTION----')
		self.description.grid(row=6, column=0, columnspan=4, sticky=W+E+N+S, padx=5, pady=5)
	
	def exitClient(self):  
		"""Teardown button handler."""
		if self.state == self.READY or self.state == self.PLAYING:
			self.sendRtspRequest(self.TEARDOWN)
	#TODO

	def pauseMovie(self):
		"""Pause button handler."""
		if self.state == self.PLAYING:
			self.sendRtspRequest(self.PAUSE)
	#TODO
	
	def playMovie(self):
		"""Play button handler."""
		if self.state == self.INIT or self.state == self.SWITCH:
			self.sendRtspRequest(self.SETUP)
		elif self.state == self.READY:
			self.sendRtspRequest(self.PLAY)
	#TODO
	
	def changeSpeed(self, changeBy):
		"""Change speed buttons handler."""
		if self.state == self.READY or self.state == self.PLAYING:
			self.standardTimeMultiplyWith = changeBy
			self.sendRtspRequest(self.CHANGESPEED)
	#TODO
	
	def describe(self):
		if self.state == self.READY or self.state == self.PLAYING:
			self.sendRtspRequest(self.DESCRIBE)
	#TODO
	
	def switchMovie(self):
		if self.state == self.READY or self.state == self.PLAYING:
			self.sendRtspRequest(self.SWITCHMOVIE)
      
    #TODO
	def listenRtp(self):		
		"""Listen for RTP packets."""
		self.totalBytesRecv = 0
		self.timeCurr = 0
		self.countLossPacket = 0
		while True:
			try:
				data = self.rtpSocket.recv(20480)
				if data:
					rtpPacket = RtpPacket()
					rtpPacket.decode(data)
					self.totalBytesRecv += len(data)
					frameNum = rtpPacket.seqNum()
					print ("Current frame number: " + str(frameNum))
					self.timeVideoPlayed = frameNum * self.standardTimeForEachFrame
					self.timeVideoPlayedReal = frameNum * (self.standardTimeForEachFrame/self.standardTimeMultiplyWith)
					self.dataRateDisplay["text"] = "Data rate: " + str(int(self.totalBytesRecv/(1000 * self.timeVideoPlayedReal))) +" KB/s"
					self.currAndTotalTime["text"] = "00:"
					if self.timeVideoPlayed < 10:
						self.currAndTotalTime["text"] += "0"
					self.currAndTotalTime["text"] += str(int(self.timeVideoPlayed)) + "/00:" + str(int(self.lengthOfVideo))
					if frameNum - self.frameNbr > 1:
						print("Lost " + str(frameNum-self.frameNbr-1) + " packets")
						self.countLossPacket += frameNum-self.frameNbr
					self.lossRateDisplay["text"] = "Packet loss rate: " + str(int((self.countLossPacket/frameNum)*100)) + " %" 
					self.frameNbr = frameNum
					self.updateMovie(self.writeFrame(rtpPacket.getPayload()))
			except:
			# Stop listening in case requesting PAUSE or TEARDOWN
				if not self.run.is_set():
					if self.teardownAcked == 1:
						self.teardownAcked = 0
						self.run.set()
					break
				
		#TODO
					
	def writeFrame(self, data):
		"""Write the received frame to a temp image file. Return the image file."""
		image_file = CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT
		file = open(image_file,"wb")
		file.write(data)
		file.close()
		return image_file
	def updateMovie(self, imageFile):
		"""Update the image file as video frame in the GUI."""
		image = Image.open(imageFile)
		photo = ImageTk.PhotoImage(image)
		self.label.configure(image = photo, height = 288)
		self.label.image = photo	
	def connectToServer(self):
		"""Connect to the Server. Start a new RTSP/TCP session."""
		# print('connect check')
		self.rtspSocket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
		try:
			self.rtspSocket.connect((self.serverAddr,self.serverPort))
		except:
			print('Server connection failed')
	def sendRtspRequest(self, requestCode):
		"""Send RTSP request to the server."""	
		# Setup request
		if requestCode == self.SETUP:
			# Create a new thread to receive RTSP reply from Server
			threading.Thread(target=self.recvRtspReply).start()
   
			# Declare an playEvent as a flag for thread that run listenRtp
			self.run = threading.Event()

			# Update RTSP sequence number
			self.rtspSeq+=1

			# Write the RTSP request to be sent 
			request = 'SETUP ' + self.fileName[self.filmIndex] + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\nTransport: RTP/UDP; client_port= ' + str(self.rtpPort)

			# Keep track of the sent request
			self.requestSent = self.SETUP
   
		# Play request
		elif requestCode == self.PLAY:
			# Create a new thread to listen to RTP packet 
			threading.Thread(target=self.listenRtp).start()
			
   			# Set state of run (True)
			self.run.set()
   
			# Update RTSP sequence number
			self.rtspSeq+=1

			# Write the RTSP request to be sent
			request = 'PLAY ' + self.fileName[self.filmIndex] + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\nSession: ' + str(self.sessionId)	
			
			# Keep track of the sent request.
			self.requestSent = self.PLAY
		
  		# Pause request
		elif requestCode == self.PAUSE:
			# Update RTSP sequence number
			self.rtspSeq+=1

			# Write the RTSP request to be sent
			request = 'PAUSE ' + self.fileName[self.filmIndex] + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\nSession: ' + str(self.sessionId)

			# Keep track of the sent request
			self.requestSent = self.PAUSE
   
		# Teardown request
		elif requestCode == self.TEARDOWN:
			# Close GUI window
			try:
			# Delete the cache image from video
				if(not self.state == self.READY):
					os.remove(CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT)
			except:
				pass
			# Update RTSP sequence number.
			self.rtspSeq+=1

			# Write the RTSP request to be sent
			request = 'TEARDOWN ' + self.fileName[self.filmIndex] + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\nSession: ' + str(self.sessionId)

			# Keep track of the sent request
			self.requestSent = self.TEARDOWN

		# Change speed request
		elif requestCode == self.CHANGESPEED:
			# Update RTSP sequence number
			self.rtspSeq+=1

			# Write the RTSP request to be sent
			request = 'CHANGESPEED x' + str(self.standardTimeMultiplyWith) + ' ' + self.fileName[self.filmIndex] + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\nSession: ' + str(self.sessionId)
   
			# Keep track of the sent request
			self.requestSent = self.CHANGESPEED

		# Describe request
		elif requestCode == self.DESCRIBE:
			# Update RTSP sequence number
			self.rtspSeq+=1

			# Write the RTSP request to be sent
			request = 'DESCRIBE ' + self.fileName[self.filmIndex] + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\nSession: ' + str(self.sessionId)
   
			# Keep track of the sent request
			self.requestSent = self.DESCRIBE
   
		# Switch movie request
		elif requestCode == self.SWITCHMOVIE:
			try:
			# Delete the cache image from video
				if(not self.state == self.READY):
					os.remove(CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT)
			except:
				pass
			# Update RTSP sequence number
			self.rtspSeq+=1
   
			# Write the RTSP request to be sent
			request = 'SWITCHMOVIE ' + self.fileName[self.filmIndex] + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\nSession: ' + str(self.sessionId)
   
			# Keep track of the sent request
			self.requestSent = self.SWITCHMOVIE

		else:
			return
		# Send the RTSP request using rtspSocket
		self.rtspSocket.send(request.encode())
		print('Data sent:')
		print(request, '\n')
	def recvRtspReply(self):
		"""Receive RTSP reply from the server."""
		while True: 	
			reply = self.rtspSocket.recv(1024)
			if reply:
				self.parseRtspReply(reply)
			# # Close the RTSP socket when requesting Teardown
			if self.requestSent == self.TEARDOWN or self.requestSent == self.SWITCHMOVIE:
				# self.rtspSocket.shutdown(socket.SHUT_RDWR)
				self.rtspSocket.close()
				break
	def parseRtspReply(self, data):
		"""Parse the RTSP reply from the server."""
		lines = data.decode().split('\n')
		seqNum = int(lines[1].split(' ')[1])
		# Process only if the server reply's sequence number is the same as the request's
		if seqNum == self.rtspSeq:
			session = int(lines[2].split(' ')[1])
			# New RTSP session ID
			if self.sessionId == 0:
				self.sessionId = session
			
			# Process only if the session ID is the same
			if self.sessionId == session:
				if int(lines[0].split(' ')[1]) == 200: 
					if self.requestSent == self.SETUP:
						# Update RTSP state.
						self.state = self.READY
						if(not self.rtpPortOpen):
							# Open RTP port.
							self.openRtpPort() 
							self.rtpPortOpen = True
						self.sendRtspRequest(self.PLAY)
						self.numFrameVideo = int(lines[3].split(' ')[6])
						self.standardTimeForEachFrame = float(lines[4].split(' ')[4])
						self.lengthOfVideo = self.numFrameVideo * self.standardTimeForEachFrame
						self.currAndTotalTime["text"] = "00:00/00:"
						self.currAndTotalTime["text"] += str(int(self.lengthOfVideo))
						self.dataRateDisplay["text"] = "Data rate: 0 KB/s"
						self.lossRateDisplay["text"] = "Packet loss rate: 0 %"
					elif self.requestSent == self.PLAY:
						self.state = self.PLAYING
					elif self.requestSent == self.PAUSE:
						self.state = self.READY
                        
						# The thread that listening to RTP packet end and is terminated
						self.run.clear()
					elif self.requestSent == self.TEARDOWN:
						self.state = self.INIT
      					# The thread that listening to RTP packet end and is terminated
						self.run.clear()
      
						# Flag the teardownAcked to close the socket.
						self.teardownAcked = 1 

						for i in os.listdir():
							if i.find(CACHE_FILE_NAME) == 0:
								try:
									os.remove(i)
								except:
									pass
						self.sessionId = 0
						self.requestSent = -1
						self.connectToServer()
						self.frameNbr = 0
						self.run.wait(0.5)
						self.teardownAcked = 0
						self.numFrameVideo = 0
						self.standardTimeForEachFrame = 0
						self.timeVideoPlayed = 0
						self.lengthOfVideo = 0
						self.standardTimeMultiplyWith = 1
						self.rtpSocket.shutdown(socket.SHUT_RDWR)
						self.rtpSocket.close()
						self.rtpPortOpen = False
						self.describeYet = False
						self.countLossPacket = 0
						self.currAndTotalTime["text"] = "--:--/--:--"
						self.dataRateDisplay["text"] = "Data rate: - KB/s"
						self.lossRateDisplay["text"] = "Packet loss rate: - %"
						self.description["text"] = "----SESSION DESCRIPTION----"
					elif self.requestSent == self.DESCRIBE:
						if(not self.describeYet):
							for i in range(3,11):
								self.description["text"] += '\n'
								self.description["text"] += lines[i]
							self.describeYet = True
					elif self.requestSent == self.SWITCHMOVIE:
						self.state = self.SWITCH
      					# The thread that listening to RTP packet end and is terminated
						self.run.clear()
      
						# Flag the teardownAcked to close the socket.
						self.teardownAcked = 1 

						for i in os.listdir():
							if i.find(CACHE_FILE_NAME) == 0:
								try:
									os.remove(i)
								except:
									pass
						self.sessionId = 0
						self.requestSent = -1
						if self.filmIndex == 3:
							self.filmIndex = 0
						else:
							self.filmIndex += 1
						self.connectToServer()
						self.frameNbr = 0
						self.run.wait(0.5)
						self.teardownAcked = 0
						self.numFrameVideo = 0
						self.standardTimeForEachFrame = 0
						self.timeVideoPlayed = 0
						self.lengthOfVideo = 0
						self.standardTimeMultiplyWith = 1
						self.rtpSocket.shutdown(socket.SHUT_RDWR)
						self.rtpSocket.close()
						self.rtpPortOpen = False
						self.describeYet = False
						self.countLossPacket = 0
						self.currAndTotalTime["text"] = "--:--/--:--"
						self.dataRateDisplay["text"] = "Data rate: - KB/s"
						self.lossRateDisplay["text"] = "Packet loss rate: - %"
						self.description["text"] = "----SESSION DESCRIPTION----"    
		#TODO
	
	def openRtpPort(self):
		"""Open RTP socket binded to a specified port."""
		#-------------
		# TO COMPLETE
		#-------------
		# Create a new datagram socket to receive RTP packets from the server
		self.rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

		# Set the timeout value of the socket to 0.5sec
		self.rtpSocket.settimeout(0.5)
		try:
			# Bind the RTP socket to the address using the RTP port given by the client user.
			self.state=self.READY
			self.rtpSocket.bind(('',self.rtpPort))
		except:
			messagebox.showwarning('Unable to Bind', 'Unable to bind PORT=%d' %self.rtpPort)
		

	def handler(self):
		"""Handler on explicitly closing the GUI window."""
		self.pauseMovie()
		if messagebox.askokcancel("Quit?", "Are you sure you want to quit?"):
			self.exitClient()
			self.master.destroy()
		else: # When the user presses cancel, resume playing.
			self.playMovie()
		#TODO
