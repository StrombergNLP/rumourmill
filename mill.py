#!/usr/bin/env python3

from rm import RumourMill

debug = True

mill = RumourMill()

mill.load_rumours('data/')
if debug:
    print(mill.rumour_store.keys())
mill.init_pi()
mill.init_printer()

while True:
    if not debug:
        mill.wait_for_activation()
    params = mill.capture_params()
    if debug:
        print(params)
    rumour = mill.find_rumour(params['genre'], params['tense'], params['temperature'])
    mill.print_rumour(rumour)
    if debug:
        break