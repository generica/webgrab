#!/usr/bin/env python

'''
AutoDump - Grab some snapshots from a webcam, place them sensibly
Copyright (C) 2012  Brett Pemberton <bpe@unimelb.edu.au>

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
'''

import webgrab
import sys
import os
import getopt
import time
import signal
import socket


def signal_handler(signal, frame):
    print "Exiting, enjoy your images"
    sys.exit(0)


def grab_images_sensibly(ip, directory, timeout, verbose=False):
    while True:
        rightnow = time.localtime()
        dirname = os.path.join(directory, str(ip), str(rightnow[0]), str(rightnow[1]), str(rightnow[2]), str(rightnow[3]))
        filename = "webcam-" + str(time.time()) + '.jpg'
        if not os.path.isdir(dirname):
            os.makedirs(dirname)
        webgrab.grab_image(ip, os.path.join(dirname, filename), verbose)
        time.sleep(timeout)


def usage():
    print "Usage: %s -i camera ip [-d dirname] [-t timeout] [-h] [-v]" % (sys.argv[0])
    print "   -i: IP address for camera"
    print "   -d: Directory to use [default: cameras]"
    print "   -t: Timeout to use in seconds [default: 1]"
    print "   -v: Verbose"
    print "   -h: Print help"


if __name__ == "__main__":

    timeout = 1
    numimages = 1
    filebase = "webcam"
    directory = "cameras"
    verbose = False
    mencoder = False
    movie = False
    image_list = []
    ip_address = False

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'i:d:t:hv')
    except getopt.GetoptError, e:
        print e
        usage()
        sys.exit(-1)
    opts = dict(opts)

    if '-v' in opts:
        verbose = True

    if '-h' in opts:
        usage()
        sys.exit(0)

    if '-i' in opts:
        ip = opts['-i']
        try:
            socket.inet_aton(ip)
        except:
            print "ERROR: Invalid IP address %s" % (ip)
            sys.exit(-1)
    else:
        usage()
        sys.exit(-1)

    if '-d' in opts:
        newdir = opts['-d']
        if os.path.isdir(newdir):
            print "WARNING: Directory %s already exists, hope this is OK" % (newdir)
            if not os.access(newdir, os.W_OK):
                print "ERROR: Directory %s is not writeable" % (newdir)
                sys.exit(-1)
        directory = newdir

    if '-t' in opts:
        try:
            newtimeout = int(opts['-t'])
        except:
            usage()
            sys.exit(-1)
        timeout = newtimeout

    print "Starting webcam grab, using directory %s, timeout %d" % (directory, timeout)
    print "Use Control-C to stop"

    signal.signal(signal.SIGINT, signal_handler)

    grab_images_sensibly(ip, directory, timeout, verbose)
