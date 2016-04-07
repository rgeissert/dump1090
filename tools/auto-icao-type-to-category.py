#!/usr/bin/python

# Copyright (C) 2016 Raphael Geissert <geissert@debian.org>
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED “AS IS” AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH
# REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY
# AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT,
# INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM
# LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR
# OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
# PERFORMANCE OF THIS SOFTWARE.


import sched, time
from os import listdir
from os.path import isfile, join
import json

JSONDIR='/usr/share/dump1090-mutability/html/db/'
LIVEJS='/run/dump1090-mutability/'
AIRCRAFTJS='aircraft.json'
ICAOMAPPINGJS='icaomapping._json'

mapping = {}
all_entries = {}

def lookup_icaot(hex):
    return all_entries[hex.upper()]['t']

def process_aircraftjs(node):
    pnode = join(LIVEJS, node)
    entries = {}

    with open(pnode, 'r') as dbf:
        entries = json.load(dbf)

    if 'aircraft' not in entries:
        return

    for aircraft in entries['aircraft']:
        if ('category' not in aircraft) or (aircraft['category'] == 'A0'):
            continue

        try:
            icao_type = lookup_icaot(aircraft['hex'])

            if icao_type not in mapping:
                print "Aircraft %s is of type %s and category %s" % (aircraft['hex'], icao_type, aircraft['category'])
                mapping[icao_type] = aircraft['category']
        except KeyError:
            pass

def reload_aircraftjs():
    process_aircraftjs(AIRCRAFTJS)
    s.enter(1, 1, reload_aircraftjs, ())

def dump_mapping():
    pnode = join(JSONDIR, ICAOMAPPINGJS)
    with open(pnode, 'w') as fh:
        json.dump(mapping, fh, sort_keys=True)
    s.enter(30, 2, dump_mapping, ())

def load_mapping():
    global mapping
    pnode = join(JSONDIR, ICAOMAPPINGJS)
    if isfile(pnode):
        with open(pnode, 'r') as fh:
            mapping = json.load(fh)

print 'Loading existing mapping...'
load_mapping()

for node in listdir(JSONDIR):
    pnode = join(JSONDIR, node)

    if not isfile(pnode):
        continue

    if not node.endswith('.json'):
        continue

    print 'Loading db file %s...' % node
    base = node[:-5]
    entries = {}

    with open(pnode, 'r') as dbf:
        entries = json.load(dbf)

    for entry in entries:
        if entry == 'children':
            continue
        all_entries[base + entry] = entries[entry]

print 'Checking history...'

for node in listdir(LIVEJS):
    pnode = join(LIVEJS, node)

    if not isfile(pnode):
        continue

    if (not node.startswith('history_')) or (not node.endswith('.json')):
        continue

    print 'Loading history file %s...' % node
    process_aircraftjs(node)

s = sched.scheduler(time.time, time.sleep)

reload_aircraftjs()
dump_mapping()
s.run()
