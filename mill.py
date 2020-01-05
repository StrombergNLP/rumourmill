#!/usr/bin/env python3

import rm

rm.load_rumours('rumours/')
rm.init_pi()
rm.init_printer()

while true:
	rm.wait_for_activation()
	params = rm.capture_params()
	rumour = rm.find_rumour(params)
	rm.print_rumour(rumour)
