#!/usr/bin/env python3

import collections
import glob
import json
import random
import re
import textwrap
import time



class RumourMill:

	rumour_store = collections.defaultdict(dict) 
		# key this by genre, temperature

	GENRES = {}

	printer = None

	tw = textwrap.TextWrapper(width=32) 

	printbutton_pin = 17

	# For toggle switch channels
	toggleup = 13
	toggledown = 26

	# For 12 step switch channels
	twlvStepOne = 18
	# twlvStepTwo = 18
	twlvStepThree = 24
	twlvStepFour = 25
	twlvStepFive = 12
	twlvStepSix = 16

	# For rotary encoder
	last_read = 0 # Keeps track of last pot. value
	tolerance = 250 # Keeps it from being jittery



	def load_rumours(self, path):
		"""Load rumours from a directory of jsonl files into the rumour store

		Parameters:
		path (str): location of the directory of jsonl files
		"""
		for filename in glob.glob(path + '/*.jsonl'):
			for line in open(filename, 'r'):
				r = json.loads(line.strip())
				g,t = r['genre'], r['temperature']
				if t not in self.rumour_store[g]:
					self.rumour_store[g] = collections.defaultdict(list)
				self.rumour_store[g][t].append(dict(r))

		for g_ in self.rumour_store:
			for t_ in self.rumour_store:
				random.shuffle(self.rumour_store[g_][t_])


	def wait_for_activation(self):
		"""Wait for a button press; include debouncing
		part lifted from https://www.cl.cam.ac.uk/projects/raspberrypi/tutorials/robot/buttons_and_switches/
		"""
		GPIO.setup(self.printbutton_pin,GPIO.IN)

		prev_input = 0
		while True:
			#take a reading
			input = GPIO.input(self.printbutton_pin)
			#if the last reading was low and this one high, print
			if ((not prev_input) and input):
				time.sleep(0.05)
				return True
			#update previous input
			prev_input = input
			#slight pause to debounce

		return True

	def capture_params(self):
		"""Read in values from the settings
		
		Returns:
		params (dict): a dictionary of setting names and values
		"""
		tense = 'present'
		if GPIO.input(self.toggleup):
			tense = 'past'
		elif GPIO.input(self.toggledown):
			tense = 'future'

		# 12 step switch here
    first_state = GPIO.input(self.twlvStepOne)
    # second_state = GPIO.input(self.twlvStepTwo)
    third_state = GPIO.input(self.twlvStepThree)
    fourth_state = GPIO.input(self.twlvStepFour)
    fifth_state = GPIO.input(self.twlvStepFive)
    sixth_state = GPIO.input(self.twlvStepSix)
    
    twelve_select = None
    if first_state:
        twelve_select = 0
    # elif second_state == False:
        # new_switch_position = "1"
    elif third_state:
        twelve_select = 2
    elif fourth_state:
        twelve_select = 3
    elif fifth_state:
        twelve_select = 4
    elif not sixth_state:
        twelve_select = 5
    else:
        twelve_select = None

    slider_position = self.chan0.value
    temperature = _remap_range(slider_position, 0, 65535, 0, 10)
    temperature = temperature / 10

	return {'genre':twelve_select, 'time':tense, 'temperature':temperature}

	def find_rumour(self, genre, temperature):
		"""Get a rumour from the store that matches the given criteria

		Parameters:
		genre (int):
		temperature (float): in the range 0..1

		Returns:
		r (dict): a random rumour matching the criteria
		"""
		return self.rumour_store[genre][temperature].pop()

	def print_rumour(self, r):
		"""take a cleaned rumour and send it to the printer

		Parameters:
		r (dict): dictionary of rumour info, containing at least keys 
					of title, body, genre, temperature
		"""
		if not self.printer:
			return False # printer hasn't been initialised yet
			
		# clean up strings
		title = re.sub(r'[^A-Za-z\s0-9,.;:.!]', '', r['title'])
		print('==>', title)
		body = re.sub(r'[^A-Za-z\s0-9,.;:.!]', '', r['body'])
		print('-->', body)

		self.printer.feed(2)
		
		# Test character double-height on & off

		self.printer.justify('C')
		self.printer.underlineOn()
		self.printer.println('Rumour from the Rumour Mill')
		self.printer.underlineOff()

		self.printer.feed(2)

		self.printer.justify('L')
		self.printer.doubleHeightOn()
		self.printer.println("\n".join(tw.wrap(text=title)))
		self.printer.doubleHeightOff()

		self.printer.feed(1)

		self.printer.setSize('S')
		self.printer.println("\n".join(tw.wrap(text=body)))

		self.printer.feed(1)

		self.printer.justify('C')
		self.printer.underlineOn()
		self.printer.println('Rumour from the Rumour Mill')
		self.printer.underlineOff()

		self.printer.feed(1)

		self.printer.justify('C')
		self.barcode_string = (str(r['genre']) + 'x')[:2]+str(r['temperature'])
		self.printer.setBarcodeHeight(30)
		self.printer.printBarcode(barcode_string.upper(), printer.CODE39)

		printer.feed(1)

		printer.justify('R')
		for k in rumour.keys():
		    if k != 'text':
		        printer.println(k, ':', rumour[k])

		printer.feed(2)

		printer.sleep()      # Tell printer to sleep
		printer.wake()       # Call wake() before printing again, even if reset
		printer.setDefault() # Restore printer to defaults
	
	def clean_rumour(self, rumour):
		""" take a rumour object, and clean it up
		"""
		if ' Text: ' in rumour['text']:
		    fulltitle, body = rumour['text'].split(' Text: ')
		    title = fulltitle.replace(rumour['prefix'], '').strip()
		elif ' Title: ' in rumour['text']:
		    fulltitle, body = rumour['text'].split(' Title: ')
		    title = fulltitle.replace(rumour['prefix'], '').strip()
		else:
		    title = rumour['text'].split('\n')[1].strip()
		    body = rumour['text'].replace(rumour['prefix'], '').replace(title, '').strip()
		rumour['body'] = body
		rumour['title'] = title
		return rumour

	def init_pi():
		import RPi.GPIO as GPIO
		GPIO.setmode(GPIO.BCM)

		import os
		import busio
		import digitalio
		import board
		import adafruit_mcp3xxx.mcp3008 as MCP
		import adafruit_mcp3xxx.analog_in

		# Creates spi bus
		self.spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
		# Creates chip select
		self.cs = digitalio.DigitalInOut(board.D22)
		# Creates mcp object
		self.mcp = MCP.MCP3008(spi, cs)
		# Creates analog input channel on pin 0
		self.chan0 = adafruit_mcp3xxxAnalogIn(mcp, MCP.P0)

		# Assigns channels to inputs for switches (toggle and 12 step)
		GPIO.setup(toggleup, GPIO.IN, pull_up_down=GPIO.PUD_UP)
		GPIO.setup(toggledown, GPIO.IN, pull_up_down=GPIO.PUD_UP)
		GPIO.setup(twlvStepOne, GPIO.IN, pull_up_down=GPIO.PUD_UP)
		GPIO.setup(twlvStepThree, GPIO.IN, pull_up_down=GPIO.PUD_UP)
		GPIO.setup(twlvStepFour, GPIO.IN, pull_up_down=GPIO.PUD_UP)
		GPIO.setup(twlvStepFive, GPIO.IN, pull_up_down=GPIO.PUD_UP)
		GPIO.setup(twlvStepSix, GPIO.IN, pull_up_down=GPIO.PUD_UP)

	def init_printer():
		import Adafruit_Thermal
		self.printer = Adafruit_Thermal.Adafruit_Thermal("/dev/serial0", 19200, timeout=5)

	def _remap_range(value, left_min, left_max, right_min, right_max):
		left_span = left_max - left_min
		right_span = right_max - right_min
	    
		valueScaled = int(value - left_min) / int(left_span)
		return int(right_min + (valueScaled * right_span))