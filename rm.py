#!/usr/bin/env python3

import board
import busio
import collections
import glob
import json
import math
import nltk
import random
import re
import textwrap
import time

import adafruit_thermal_printer
import RPi.GPIO as GPIO


class RumourMill:

    rumour_store = collections.defaultdict(dict) 
        # key this by genre, temperature

    GENRES = ['Politics', 'Conspiracy', 'Science', 'CNN Business', 'Entertainment Tonight',
              'Daily Mail health', 'Fox News sports', 'The Independent', 'Russia Today'] # corresponds to ordering genre_prompts in rm_generation.py

    printer = None

    tw = textwrap.TextWrapper(width=32) 

    printbutton_pin = 17

    # For toggle switch channels
    toggleup = 13
    toggledown = 26

    # For 12 step switch channels
    twlvStepOne = 18
    twlvStepTwo = 23
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
                g, t = r['genre'], r['temperature']
                g = str(g)
                t = str(t)
                if t not in self.rumour_store[g]:
                    self.rumour_store[g][t] = []
                self.rumour_store[g][t].append(dict(r))

        for g_ in self.rumour_store:
            for t_ in self.rumour_store[g]:
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
        if not GPIO.input(self.toggleup):
            tense = 'past'
        elif not GPIO.input(self.toggledown):
            tense = 'future'

        # 12 step switch here
        first_state = GPIO.input(self.twlvStepOne)
        second_state = GPIO.input(self.twlvStepTwo)
        third_state = GPIO.input(self.twlvStepThree)
        fourth_state = GPIO.input(self.twlvStepFour)
        fifth_state = GPIO.input(self.twlvStepFive)
        sixth_state = GPIO.input(self.twlvStepSix)
        
        twelve_select = None
        if not first_state:
            twelve_select = 0
        elif not second_state:
            twelve_select = "1"
        elif not third_state:
            twelve_select = 2
        elif not fourth_state:
            twelve_select = 3
        elif not fifth_state:
            twelve_select = 4
        elif not sixth_state:
            twelve_select = 5
        else:
            twelve_select = None

        slider_position = self.chan0.value
        temperature = self._remap_range(slider_position, 0, 65535, 0, 18500)
        if temperature > 0:
            temperature = math.log(temperature)
        temperature = int(temperature) / 10

        return {'genre':twelve_select, 'tense':tense, 'temperature':temperature}

    def find_rumour(self, genre, tense, temperature):
        """Get a rumour from the store that matches the given criteria

        Parameters:
        genre (int):
        temperature (float): in the range 0..1

        Returns:
        r (dict): a random rumour matching the criteria
        """
        genre = str(genre)
        if genre in ('3','4'):
            genre += tense
        temperature = str(temperature)
        print(genre, 'in', self.rumour_store.keys())
        print(temperature, 'in', self.rumour_store[genre].keys())
        print('entries:', len(self.rumour_store[genre][temperature]))
        return self.rumour_store[genre][temperature].pop()

    def print_rumour(self, r):
        """take a cleaned rumour and send it to the printer

        Parameters:
        r (dict): dictionary of rumour info, containing at least keys 
                    of title, body, genre, temperature
        """
        if not self.printer:
            return False # printer hasn't been initialised yet
        
        r = self.clean_rumour(r)
        title, body = r['title'], r['body']
        # clean up strings
        title = re.sub(r'[^A-Za-z\s0-9,.;:.!\'"&\[\]\(\)]', '', r['title']).strip()
        print('==>', title)
        body = re.sub(r'[^A-Za-z\s0-9,.;:.!]', '', r['body']).strip()
        print('-->', body)

        self.printer.feed(2)
        
        # Test character double-height on & off

        self.printer.justify = adafruit_thermal_printer.JUSTIFY_CENTER
        self.printer.underline = adafruit_thermal_printer.UNDERLINE_THIN
        self.printer.print('Rumour from the Rumour Mill')
        self.printer.underline = None

        self.printer.feed(2)

        self.printer.justify = adafruit_thermal_printer.JUSTIFY_LEFT
        self.printer.double_height = True
        self.printer.print("\n".join(self.tw.wrap(text=title)))
        self.printer.double_height = False

        self.printer.feed(1)

        self.printer.size = adafruit_thermal_printer.SIZE_SMALL
        self.printer.print("\n".join(self.tw.wrap(text=body)))

        self.printer.feed(1)

        self.printer.justify = adafruit_thermal_printer.JUSTIFY_CENTER
        self.printer.underline = adafruit_thermal_printer.UNDERLINE_THIN
        self.printer.print('Rumour from the Rumour Mill')
        self.printer.underline = None

        self.printer.feed(1)

#        self.printer.justify = adafruit_thermal_printer.JUSTIFY_CENTER
#        self.barcode_string = (str(r['genre']) + 'x')[:2]+str(r['temperature'])
#        self.printer.setBarcodeHeight(30)
#        self.printer.printBarcode(barcode_string.upper(), printer.CODE39)

        self.printer.feed(2)

        self.printer.justify = adafruit_thermal_printer.JUSTIFY_LEFT
        if isinstance(r['genre'], int):
            genrename = self.GENRES[r['genre']]
            tense = None
        else:
            genrename = self.GENRES[int(r['genre'][0])]
            tense = r['genre'][1:]
            
        self.printer.print('Wackiness: ' + str(r['temperature'] * 10) + '/10')
        self.printer.print('Genre: ' + genrename)
        if tense:
            self.printer.print('Time: ' + tense)
        else:
            self.printer.print('No flux capacitor for this genre')

        self.printer.feed(1)

        self.printer.justify = adafruit_thermal_printer.JUSTIFY_RIGHT
        for k in r.keys():
            if k not in ('text', 'body', 'title', 'temperature', 'genre', 'nucprob'):
                self.printer.print(str(k) + ':' + str(r[k]))

        self.printer.bold = True
        self.printer.justify = adafruit_thermal_printer.JUSTIFY_CENTER
        self.printer.print('-- END OF RUMOUR --')


        self.printer.feed(3)

#        printer.sleep()      # Tell printer to sleep
#        printer.wake()       # Call wake() before printing again, even if reset
#        printer.setDefault() # Restore printer to defaults
    
    def clean_rumour(self, rumour):
        """ take a rumour object, and clean it up
        """
        text = rumour['text']
        strip_strings = ('Share this article', 'RELATED ARTICLES', 
            'Story highlights', '(CNN)', '&gt;', 
            "Chat with us in Facebook Messenger. Find out what's happening in the world as it unfolds.",
            'JUST WATCHED', 'MUST WATCH', 'Read More', 'Watch more!', 'SPONSORED:',
            'Getty Images')
        for s in strip_strings:
            text = text.replace(s, '')
        text = re.sub(r'By [A-Za-z]+ [A-Za-z]+, .+?\n ', '', text)
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', '\1', text) # markdown

        if ' Text: ' in text:
            fulltitle, body = text.split(' Text: ')
            title = fulltitle.replace(rumour['prefix'], '').strip()
        elif ' Title: ' in text:
            fulltitle, body = text.split(' Title: ')
            title = fulltitle.replace(rumour['prefix'], '').strip()
        else:
            title = text.split('\n')[1].strip()
            body = text.replace(rumour['prefix'], '').replace(title, '').strip()

        title_sents = nltk.sent_tokenize(title)
        if len(title_sents) > 1:
            title = title_sents[0]
            body = ' '.join(title_sents[1:]) + ' ' + body

        if not title.strip():
            if 'cnn.com' in rumour['prefix']:
                lines = body.split("\n")
                title = lines[0]
                body = "\n".join(lines[1:]).strip()
            else:
                body_sents = nltk.sent_tokenize(body)
                title = body_sents[0]
                body = ' '.join(body_sents[1:])

        if "\n" in title:
            title_lines = title.split("\n")
            title = title_lines[0]
            body = '\n'.join(title_lines[1:]) + "\n" + body

        rumour['body'] = body.strip()
        rumour['title'] = title.strip()
        #rumour['text'] = text
        return rumour

    def init_pi(self):
        GPIO.setmode(GPIO.BCM)

        import os
        import digitalio
        import adafruit_mcp3xxx.mcp3008 as MCP
        import adafruit_mcp3xxx.analog_in

        # Creates spi bus
        self.spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
        # Creates chip select
        self.cs = digitalio.DigitalInOut(board.D22)
        # Creates mcp object
        self.mcp = MCP.MCP3008(self.spi, self.cs)
        # Creates analog input channel on pin 0
        self.chan0 = adafruit_mcp3xxx.analog_in.AnalogIn(self.mcp, MCP.P0)

        # Assigns channels to inputs for switches (toggle and 12 step)
        GPIO.setup(self.toggleup, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.toggledown, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.twlvStepOne, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.twlvStepTwo, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.twlvStepThree, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.twlvStepFour, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.twlvStepFive, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.twlvStepSix, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def init_printer(self):
        import serial
        
        self.thermal_printer = adafruit_thermal_printer.get_printer_class(2.69) # corresponds to printer firmware
        self.uart = serial.Serial("/dev/serial0", baudrate=19200, timeout=3000)
        self.printer = self.thermal_printer(self.uart, auto_warm_up=False)
        self.printer.warm_up()

    def _remap_range(self, value, left_min, left_max, right_min, right_max):
        left_span = left_max - left_min
        right_span = right_max - right_min
        
        valueScaled = int(value - left_min) / int(left_span)
        return int(right_min + (valueScaled * right_span))