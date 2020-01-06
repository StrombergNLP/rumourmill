#!/usr/bin/env python3

import rm
import time

m = rm.RumourMill()
m.init_pi()

while True:
  print(m.capture_params())
  time.sleep(0.05)
