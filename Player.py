#!/usr/bin/env python

import subprocess
import glob
import random
import fcntl
import os

class Player(object):

	def __init__(self):
		self.music_dir = "/data/music"
		self.reset()
		
	def reset(self):
		self.player = None
		self.playlist = list()
		self.playlist_pos = 0
		self.loaded_file = ""
		self.playing = False
		
	def startup(self):
		if not self.player:
			self.player = subprocess.Popen("mpg123 --remote", shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
			# set the O_NONBLOCK flag of self.player.stdout file descriptor:
			flags = fcntl.fcntl(self.player.stdout, fcntl.F_GETFL) # get current p.stdout flags
			fcntl.fcntl(self.player.stdout, fcntl.F_SETFL, flags | os.O_NONBLOCK)
			self.player.stdin.write('silence\n')
			self.read()
	
	def shutdown(self):
		self.stop()
		if self.player:
			self.player.stdin.write('quit\n')
		self.reset()
		
	def play(self):
		if self.player and not self.playing:
			while self.playlist_pos+1 > len(self.playlist):
				self.add_file()
			if self.playlist[self.playlist_pos] != self.loaded_file:
				self.loaded_file = self.playlist[self.playlist_pos]
				self.player.stdin.write('lp '+self.loaded_file+'\n')
			print "pos "+str(self.playlist_pos)
			self.player.stdin.write('p\n')
			self.read()
			self.playing = True
		
	def pause(self):
		if self.player and self.playing:
			self.playing = False
			self.player.stdin.write('p\n')
			self.read()
			
	
	def stop(self):
		if self.player:
			self.playing = False
			self.player.stdin.write('stop\n')
			self.loaded_file = ""
			self.read()
		
	def next(self):
		if self.player:
			self.stop()
			self.playlist_pos += 1
			self.play()
	
	def prev(self):
		if self.player:
			self.stop()
			if self.playlist_pos > 0:
				self.playlist_pos -= 1
			self.play()
			
	def check(self):
		output = self.read()
		if len(output) == 1 and output[0] == "@P 0" and self.playing:
			self.next()
		
				
	def read(self):
		output = list()
		while self.player:
			try:
				line = self.player.stdout.readline().strip()
				if  line == "": 
					break
				output.append(line)
			except IOError:
				# the os throws an exception if there is no data
				#print '[No more data]'
				break
		if len(output) > 0 :
			print output
		return output
			
	def add_file(self):
		files = glob.glob(self.music_dir+"/*/*/*.mp3")
		self.playlist.append(files[random.randint(0, len(files)-1)])

