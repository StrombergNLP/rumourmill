#!/usr/bin/env python3

import glob
import json
import rm

mill = rm.RumourMill()

for filename in glob.glob('data/*.jsonl'):
	for line in open(filename, 'r'):
		r = json.loads(line.strip())
		r = mill.clean_rumour(r)

		print('prefix ::', r['prefix'])
		print('text   ::', r['text'])
		print('title  ::', r['title'])
		print('body   ::', r['body'])

		print('-' * 50)