#!/usr/bin/env python

import RPi.GPIO as GPIO
import commands
import signal
import sys
import pylirc
import time

import FrontPanel

panel = None

def signal_handler(signal, frame):
	panel = FrontPanel.FrontPanel()
	panel.turn_off()
        sys.exit(0)


def main():

	signal.signal(signal.SIGINT, signal_handler)
	signal.signal(signal.SIGTERM, signal_handler)
	
	pylirc.init("front-panel-interface", "/etc/front-panel/pylirc.conf", 0) # non-blocking

	ip = commands.getoutput("/sbin/ifconfig").split("\n")[1].split()[1][5:]

	# use P1 header pin numbering convention
	GPIO.setmode(GPIO.BOARD)

	panel = FrontPanel.FrontPanel()
	panel.turn_on()

	while True:

		panel.check_for_input()

		panel.display_text(ip, 1, 0)

		panel.display_clock()
		
		panel.check_player()

		time.sleep(0.1)

if(__name__ == "__main__"):
	main()
