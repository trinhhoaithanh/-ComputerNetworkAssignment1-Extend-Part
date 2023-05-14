class VideoStream:
	def __init__(self, filename):
		self.filename = filename
		try:
			self.file = open(filename, 'rb')
		except:
			raise IOError
		self.frameNum = 0
		self.frames = []	
		self.numFrameVideo = self.totalFrame()
	def nextFrame(self):
		"""Get next frame."""
		self.frameNum += 1
		if self.frameNum - 1 >= self.numFrameVideo:
			return ''
		return self.frames[self.frameNum-1]
		
	def frameNbr(self):
		"""Get frame number."""
		return self.frameNum

	def totalFrame(self):
		"""Get total number of frames in the video"""
		try:
			self.file = open(self.filename, 'rb')
		except:
			raise IOError
		count = 0
		start = 0
		data = self.file.read()
		# print(data)
		while True:
			# search for the next SOF marker
			sof = data.find(b'\xff\xd8', start)
			if sof == -1:
				break

			# search for the next EOI marker
			eoi = data.find(b'\xff\xd9', sof)
			if eoi == -1:
				break
			count += 1
			# extract the frame data between the SOF and EOI markers
			self.frames.append(data[sof:eoi+2])
			# print(str(sof) + ' ' + str(data[sof:eoi]) + ' ' + str(eoi))
			# move the search start position to the next frame
			start = eoi + 2
		return count
	def getName(self):
		return self.filename
      
			


		
	
	