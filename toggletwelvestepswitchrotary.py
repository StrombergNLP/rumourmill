import RPi.GPIO as GPIO
import time

# These are for the MCP 3008 A/D chip
import os
import busio
import digitalio
import board
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn

# Creates spi bus
spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
# Creates chip select
cs = digitalio.DigitalInOut(board.D22)
# Creates mcp object
mcp = MCP.MCP3008(spi, cs)
# Creates analog input channel on pin 0
chan0 = AnalogIn(mcp, MCP.P0)

GPIO.setmode(GPIO.BCM)

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

# Assigns channels to inputs for switches (toggle and 12 step)
GPIO.setup(toggleup, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(toggledown, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(twlvStepOne, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(twlvStepThree, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(twlvStepFour, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(twlvStepFive, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(twlvStepSix, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Remaps rotary encoder from original (left) range to new (right) range
def remap_range(value, left_min, left_max, right_min, right_max):
    left_span = left_max - left_min
    right_span = right_max - right_min
    
    valueScaled = int(value - left_min) / int(left_span)
    return int(right_min + (valueScaled * right_span))

twlvStep_position = "unknown"
tgglSwitch_position = "unknown"
print(last_read)

while True:
    # Toggle switch here
    toggle_up_state = GPIO.input(toggleup)
    toggle_down_state = GPIO.input(toggledown)
    
    new_toggle_position = "unknown"
    
    if toggle_up_state == False:
        new_toggle_position = "left"
    elif toggle_down_state == False:
        new_toggle_position = "right"
    else:
        new_toggle_position = "center"
    if new_toggle_position != tgglSwitch_position:
        tgglSwitch_position = new_toggle_position
        print(tgglSwitch_position)
    
    # 12 step switch here
    first_state = GPIO.input(twlvStepOne)
    # second_state = GPIO.input(twlvStepTwo)
    third_state = GPIO.input(twlvStepThree)
    fourth_state = GPIO.input(twlvStepFour)
    fifth_state = GPIO.input(twlvStepFive)
    sixth_state = GPIO.input(twlvStepSix)
    
    if first_state == False:
        new_switch_position = "1"
    # elif second_state == False:
        # new_switch_position = "2"
    elif third_state == False:
        new_switch_position = "3"
    elif fourth_state == False:
        new_switch_position = "4"
    elif fifth_state == False:
        new_switch_position = "5"
    elif sixth_state == False:
        new_switch_position = "6"
    else:
        new_switch_position = "mid"
    if new_switch_position != twlvStep_position:
        twlvStep_position = new_switch_position
        print(twlvStep_position)
        
    # Rotary encoder here
    slider_changed = False
    slider_position = chan0.value
    slider_adjust = abs(slider_position - last_read)
    
    if slider_adjust > tolerance:
        slider_changed = True
    
    if slider_changed:
        # Convert 16bit adc0 (0-65535) to 0-100
        set_read = remap_range(slider_position, 0, 65535, 0, 100)
        print("Slider position = {slider}" .format(slider = set_read))
        
        # Save reading for next loop
        last_read = slider_position
        
    time.sleep(0.5)


