#!/usr/bin/env python3

from rm import RumourMill

mill = RumourMill()

mill.load_rumours('rumours/')
mill.init_pi()
mill.init_printer()

while true:
	mill.wait_for_activation()
	params = mill.capture_params()
	rumour = mill.find_rumour(params)
	mill.print_rumour(rumour)
