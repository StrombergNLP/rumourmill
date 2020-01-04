#!/usr/bin/python

from Adafruit_Thermal import *

import json
import random
import re
import textwrap

tw = textwrap.TextWrapper(width=32) 

rumours = []
for line in open('nohead_t05.jsonl', 'r'):
    rumours.append(json.loads(line.strip()))

random.shuffle(rumours)

rumour = rumours.pop()

print(rumour)

if ' Text: ' in rumour['text']:
    fulltitle, body = rumour['text'].split(' Text: ')
    title = fulltitle.replace(rumour['prefix'], '').strip()
elif ' Title: ' in rumour['text']:
    fulltitle, body = rumour['text'].split(' Title: ')
    title = fulltitle.replace(rumour['prefix'], '').strip()
else:
    title = rumour['text'].split('\n')[1].strip()
    body = rumour['text'].replace(rumour['prefix'], '').replace(title, '').strip()

printer = Adafruit_Thermal("/dev/serial0", 19200, timeout=5)

title = re.sub(r'[^A-Za-z\s0-9,.;:.!]', '', title)
print('==>', title)
body = re.sub(r'[^A-Za-z\s0-9,.;:.!]', '', body)
print('-->', body)


# Test character double-height on & off
printer.feed(2)
printer.justify('C')
printer.underlineOn()
printer.println('Rumour from the Rumour Mill')
printer.underlineOff()
printer.feed(2)

printer.justify('L')
printer.doubleHeightOn()
printer.println("\n".join(tw.wrap(text=title)))
printer.doubleHeightOff()

printer.feed(1)

printer.setSize('S')
printer.println("\n".join(tw.wrap(text=body)))

printer.feed(1)

printer.justify('C')
printer.underlineOn()
printer.println('Rumour from the Rumour Mill')
printer.underlineOff()

printer.feed(1)

printer.justify('C')

barcode_string = (str(rumour['genre']) + 'x')[:2]+str(rumour['temperature'])
printer.setBarcodeHeight(30)
printer.printBarcode(barcode_string.upper(), printer.CODE39)

printer.feed(1)

printer.justify('R')
for k in rumour.keys():
    if k != 'text':
        printer.println(k, ':', rumour[k])

#printer.setLineHeight(50)
#printer.println("Taller\nline\nspacing")
#printer.setLineHeight() # Reset to default

# Barcode examples
# CODE39 is the most common alphanumeric barcode


# Print UPC line on product barcodes
#printer.printBarcode("123456789123", printer.UPC_A)

# Print the 75x75 pixel logo in adalogo.py
#import gfx.adalogo as adalogo
#printer.printBitmap(adalogo.width, adalogo.height, adalogo.data)

# Print the 135x135 pixel QR code in adaqrcode.py
#import gfx.adaqrcode as adaqrcode
#printer.printBitmap(adaqrcode.width, adaqrcode.height, adaqrcode.data)
#printer.println("Adafruit!")

printer.feed(2)


printer.sleep()      # Tell printer to sleep
printer.wake()       # Call wake() before printing again, even if reset
printer.setDefault() # Restore printer to defaults
