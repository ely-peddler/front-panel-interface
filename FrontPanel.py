#!/usr/bin/env python

import RPi.GPIO as GPIO
import time
import serial
import datetime
import subprocess
import sys
import os
import pylirc

import Player

class FrontPanel(object):

	_instance = None

	def __new__(cls, *args, **kwargs):
		if not cls._instance:
			print("Creating singleton")
			cls._instance = super(FrontPanel, cls).__new__(cls, *args, **kwargs)
		return cls._instance

	init_called = False
	def __init__(self):
		if self.init_called:
			return
		else:
			self.init_called = True
		self.player = Player.Player()
		self.song = None
		self.on = False
		self.blank_cell = "        "
		self.text = [ [ self.blank_cell, self.blank_cell ], [ self.blank_cell, self.blank_cell ] ]

        	self.standby_pin = 23
        	GPIO.setup(self.standby_pin, GPIO.OUT)
        	GPIO.output(self.standby_pin, GPIO.HIGH)

		time.sleep(1)

		self.ser = serial.Serial("/dev/ttyAMA0", 9600, timeout=5)
#		time.sleep(1)
		self.setup_screen(250)
		print("2")

		self.col_pins = [ 11, 12, 13, 15, 16 ] #[ 16, 18, 22, 24, 26 ]
		self.row_pins = [ 18, 22 ] #[ 21, 23 ]

        	for col_pin in self.col_pins:
                	print(col_pin)
                	GPIO.setup(col_pin, GPIO.OUT)
                	GPIO.output(col_pin, GPIO.LOW)

        	for row_pin in self.row_pins:
                	print(row_pin)
                	GPIO.setup(row_pin, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)

		self.actions = [ [ "SELECT", "BACK", "OPEN", "REWIND", "FORWARD" ],
                                 [ "NEXT", "PREVIOUS", "PAUSE", "PLAY", "STOP" ] ]
        	self.action = ""	
		self.action_count = 0

        	
		self.power_check_pin = 19
        	GPIO.setup(self.power_check_pin, GPIO.IN)

		
#        	self.powered_up_pin = 12
 #       	GPIO.setup(self.powered_up_pin, GPIO.OUT)
  #      	GPIO.output(self.powered_up_pin, GPIO.HIGH)
		
	
	def shutdown():
		self.turn_off
		GPIO.output(self.standby_pin, GPIO.HIGH)

	def clear_screen(self):
		print("Clear screen")
		self.ser.write(chr(4)+chr(0xFF))
		self.text = [ [ self.blank_cell, self.blank_cell ], [ self.blank_cell, self.blank_cell ] ]
		print(self.text)

	def setup_screen(self, brightness):
		print("Setup screen")
		#time.sleep(1)
		self.ser.write(chr(5)+chr(2)+chr(16)+chr(0xFF))
		self.clear_screen()
		# set brightness
		self.ser.write(chr(7)+chr(brightness)+chr(0xFF))
		#time.sleep(1)

	def move_cursor(self, row, col):
#		print("Cursor "+str(row)+", "+str(col))
		self.ser.write(chr(2)+chr(row+1)+chr((col*8)+1)+chr(0xff))
		#self.ser.write(chr(2)+chr(line)+chr(col)+chr(0xFF))

	def write_text(self, text):
#		print("Write text: "+text)
		self.ser.write(chr(1)+text+chr(0xFF))

	def turn_on(self):
		print("on")
		self.on = True
		GPIO.output(self.standby_pin, GPIO.LOW)
		#self.ser = serial.Serial("/dev/ttyAMA0", 9600, timeout=5)
		#time.sleep(1)
		self.setup_screen(250)
		time.sleep(0.8)
		self.player.startup()

		
	def turn_off(self):
		self.player.shutdown()
		print("off")
		self.on = False
		#self.text = ""
		#self.clear_screen()
		#self.ser.write(chr(7)+chr(0)+chr(0xFF))
		self.setup_screen(0)
		GPIO.output(self.standby_pin, GPIO.HIGH)
		#self.ser = None
		#time.sleep(1)

	def toggle(self):
		if(self.on):
			self.turn_off()
		else:
			self.turn_on()
		
	def display_clock(self):
		 if(self.on):
		 	self.display_text(datetime.datetime.now().strftime("%H:%M:%S"), 0, 1)
			
	def display_text(self, text, row, col):
#		print("Display '"+text+"' @ "+str(row)+","+str(col))
		if(self.on):
			if(self.text[row][col] != text):
				self.text[row][col] = text
#				print(self.text)
				self.move_cursor(row, col)
				#self.ser.write(chr(2)+chr(row+1)+chr((col*8)+1)+chr(0xff))
				self.write_text(text)
				return
				self.text = text
				self.move_cursor(row+1,(column*8)+1)
				self.write_text("        ")
				time.sleep(3)
				self.move_cursor(row+1,(column*8)+1)
				self.write_text(text)
				time.sleep(3)

	def check_player(self):
		if self.on:
			song = self.player.check()
			if song:
				if not self.song or self.song.title != song.title:
					self.display_text("                ", 1, 0)
					self.scroll = 0
					self.scroll_delta = 0.3
					self.scroll_display_length = 16
				if  len(song.title) > 0 and len(song.title) < 16:
					self.scroll = 0
					self.scroll_delta = 0
					self.scroll_display_length = len(song.title)
				else:
					if int(self.scroll) < 0:
						self.scroll_delta = -self.scroll_delta
						self.scroll = 0
					elif len(song.title)-int(self.scroll) < 16:
						self.scroll_delta = -self.scroll_delta
						self.scroll = len(song.title) - 16
				self.display_text(song.title[int(self.scroll):int(self.scroll)+self.scroll_display_length], 1, 0)
				self.scroll += self.scroll_delta
			else:
				self.display_text("                ", 1, 0)
			self.song = song
		
	def check_for_input(self):
		next_action = self.check_ir_sensor()
#		print("IR "+str(next_action))
		if(next_action == None):
			next_action = self.check_buttons()
#			print("Button "+str(next_action))
#		if(next_action != None):
		self.handle_action(next_action)

	def check_buttons(self):
		if(GPIO.input(self.power_check_pin)):
			print("POWER")
			return "POWER"
		else:
			next_action = None
			if(self.on):
				for col in range(len(self.col_pins)):
					GPIO.output(self.col_pins[col], GPIO.HIGH)
					for row in range(len(self.row_pins)):
						if(GPIO.input(self.row_pins[row])):
							next_action = self.actions[row][col]
					GPIO.output(self.col_pins[col], GPIO.LOW)
			return next_action

	def check_ir_sensor(self):
		s = pylirc.nextcode()
		if(s != None):
			if(self.on or s[0] == "POWER"):
				return s[0]
		return None

	def handle_action(self, action):
		if(action != self.action and (action != None or self.action_count > 5)):
			if(self.action == "POWER" and self.action_count >= 20):
				self.on = True
				self.display_text("Shutdown cancel",1,0)
				time.sleep(1)
			self.action_count = 0
			self.action = action
		else: 
			self.action_count += 1

		if(self.action == "POWER"):
			if(self.action_count == 0):
				self.toggle()
			elif(self.action_count == 10 and self.on):
				self.turn_off()
			elif(self.action_count == 20):
				self.turn_on()  # to display shut down message
 				self.display_text("Shutting down",1,0)
				self.on = False # to stop an other input or display
 			elif(self.action_count == 30):
 				self.turn_off() 				
				os.system( "poweroff" )
  				sys.exit()
		elif(self.on and self.action_count == 0):
			action = self.action
			action_text = self.blank_cell
			if(self.action != None):
				action_text = self.action
			if(self.action == "OPEN"):
				subprocess.call("eject")
			if(action_text == "PLAY"):
				self.player.play()
			elif(action_text == "PAUSE"):
				self.player.pause()
			elif(action_text == "STOP"):
				self.player.stop()
			elif(action_text == "NEXT" or action_text == "FORWARD"):
				self.player.next()
			elif(action_text == "PREV" or action_text == "REWIND"):
				self.player.prev()
			elif(action_text == ""):
				action_text = self.blank_cell
			if(action_text != self.blank_cell):
				print("Action '"+action_text+"'")
			self.display_text(action_text, 0,0)

