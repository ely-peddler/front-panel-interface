#!/usr/bin/env python

import subprocess
import glob
import random
import fcntl
import os
import json

class Song(object):
	
	def __init__(self):
		self.title = ""
		self.album = ""
		self.artist = ""

class Player(object):

	def __init__(self):
		self.config_filename = "/etc/front-panel/player.conf"
		self.reset()
		
	def reset(self):
		self.player = None
		self.loaded_file = ""
		self.playing = False
		self.clear_playlist()
		
	def clear_playlist(self):
		self.playlist = list()
		self.playlist_pos = 0
		self.current_song = None
		
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
				if not self.add_file():
					self.stop()
					return
			if self.playlist[self.playlist_pos] != self.loaded_file:
				self.loaded_file = self.playlist[self.playlist_pos]
				self.player.stdin.write('lp '+self.loaded_file+'\n')
				self.current_song = Song()
			print "pos "+str(self.playlist_pos)
			print "file "+self.playlist[self.playlist_pos]
			print "playlist size "+str(len(self.playlist))
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
			self.clear_playlist()
			self.stop_current_song()
			
	def stop_current_song(self):
		if self.player:
			self.playing = False
			self.player.stdin.write('stop\n')
			self.loaded_file = ""
			self.read()
		
	def next(self):
		if self.player:
			self.stop_current_song()
			self.playlist_pos += 1
			self.play()
	
	def prev(self):
		if self.player:
			self.stop_current_song()
			if self.playlist_pos > 0:
				self.playlist_pos -= 1
			self.play()
			
	def check(self):
		output = self.read()
		p = -1
		for msg in output:
			if msg.startswith("@P "):
				p = int(msg[3:4])
				print msg+" p="+str(p)
		
		if p == 0 and self.playing:
			print "next p="+str(p)
			self.next()
		return self.current_song	
		
				
	def read(self):
		output = list()
		while self.player:
			try:
				line = self.player.stdout.readline().strip()
				if  line == "": 
					break
				output.append(line)
				if self.current_song:
					if line.startswith("@I ID3v2.title:"):
						print line
						print line[15:]
						self.current_song.title = line[15:]
					if line.startswith("@I ID3v2.album:"):
						self.current_song.album = line[15:]
					if line.startswith("@I ID3v2.artist:"):
						self.current_song.artist = line[16:]
			except IOError:
				# the os throws an exception if there is no data
				#print '[No more data]'
				break
		if len(output) > 0 :
			print output
		return output
			
	def add_file(self):
		config = None
		with open(self.config_filename) as config_file:
			config = json.load(config_file)
		files = list()
		if config:
			for artist in config["artists"]:
				files.extend(glob.glob(config["music folder"]+"/"+artist+"/*/*.mp3"))
#			for album in config["albums"]:
#				files.extend(glob.glob(config["music folder"]+"/*/"+album+"/*.mp3"))
		if len(files) == 0:
			files.extend(glob.glob("/data/music/*/*/*.mp3"))
		if len(files) <= len(self.playlist):
			self.clear_playlist()
			if not config["loop"]:
				return False
		if config["shuffle"]:
			new_file = files[random.randint(0, len(files)-1)]
			while new_file in self.playlist:
				new_file = files[random.randint(0, len(files)-1)]
			self.playlist.append(new_file)
		else:			
			self.playlist.append(sorted(files)[len(self.playlist)])
		return True


		
		

