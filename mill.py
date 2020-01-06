#!/usr/bin/env python3

from rm import RumourMill

mill = RumourMill()

mill.load_rumours('data/')
mill.init_pi()
mill.init_printer()

debug = True

while true:
    if not debug:
        mill.wait_for_activation()
    params = mill.capture_params()
    if debug:
        print(params)
    rumour = mill.find_rumour(params)
    mill.print_rumour(rumour)
    if debug:
        break