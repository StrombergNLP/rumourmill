#!/usr/bin/env python3

import collections
import glob
import json
import random
import re
import textwrap

class RumourMill:

	rumour_store = collections.defaultdict(dict) 
		# key this by genre, temperature

	GENRES = {}

	printer = None

	tw = textwrap.TextWrapper(width=32) 


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
		return True

	def capture_params(self):
		"""Read in values from the settings
		
		Returns:
		params (dict): a dictionary of setting names and values
		"""
		return {}

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
		pass

	def init_printer():
		import Adafruit_Thermal
		self.printer = Adafruit_Thermal.Adafruit_Thermal("/dev/serial0", 19200, timeout=5)
