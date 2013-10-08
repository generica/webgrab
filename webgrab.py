#!/usr/bin/env python

'''
WebGrab - Grab some snapshots from a webcam
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

import sys
import re
import os
import getopt
import time
import signal
import tempfile
import commands
import socket
try:
    import pycurl
except:
    print "ERROR: Pycurl is required"
    sys.exit(-1)
from StringIO import StringIO

mencoder_args = '-nosound -ovc lavc -lavcopts vcodec=mpeg4:mbd=2:trell:autoaspect:vqscale=3 -vf scale=640:480 -mf type=jpeg:fps=24'


def signal_handler(signal, frame):
    print "Exiting, enjoy your images"
    sys.exit(0)


def grab_image(ip, image_filename, verbose=False):
    username = 'admin'
    password = 'PASSW0RD'
    top_level_url = "http://%s/" % (ip)
    snapshot = top_level_url + "cgi-bin/view/ss.cgi"

    if verbose:
        print "Grabbing an image to %s" % (image_filename)

    storage = StringIO()
    c = pycurl.Curl()
    c.setopt(pycurl.URL, snapshot)
    c.setopt(pycurl.HTTPHEADER, ['Accept: application/json'])
    c.setopt(pycurl.VERBOSE, 0)
    c.setopt(pycurl.USERPWD, username + ':' + password)
    c.setopt(c.WRITEFUNCTION, storage.write)
    try:
        c.perform()
    except pycurl.error, error:
        errno, errstr = error
        if errno == 7 or errno == 6:
            print "ERROR: Can't connect to the camera, is the IP address correct?"
            sys.exit(-1)

    content = storage.getvalue()

    search = re.findall('\<img src="/(snapshot.jpg\?v=[0-9]*)"', content)
    if not search:
        print "WARNING: Got an odd response from the camera: " + content
        return False
    img = search[0]
    image = top_level_url + img

    if os.path.isfile(image_filename):
        print "ERROR: File %s exists" % (image_filename)
        sys.exit(0)

    i = open(image_filename, 'w')

    storage2 = StringIO()
    c.setopt(pycurl.URL, image)
    c.setopt(c.WRITEFUNCTION, i.write)
    c.perform()

    i.close()

    return True


def grab_images(ip, directory, filebase, timeout, numimages, verbose=False):
    if not os.path.isdir(directory):
        os.mkdir(directory)

    image_list = []

    for i in range(0, numimages):
        filename = filebase + "-" + str(time.time()) + '.jpg'
        if grab_image(ip, os.path.join(directory, filename), verbose):
            image_list.append(os.path.join(directory, filename))
        time.sleep(timeout)

    return image_list


def make_movie(image_list, movie, mencoder, verbose=False):
    framelist = tempfile.NamedTemporaryFile(delete=False)
    images = "\n".join(item for item in image_list)
    framelist.write(images)
    framelist.close()

    command = "%s %s mf://@%s -o %s" % (mencoder, mencoder_args, framelist.name, movie)
    if verbose:
        print "Executing: %s" % (command)
    (status, output) = commands.getstatusoutput(command)
    if status != 0:
        print "WARNING: Got status %d from mencoder" % (status)
        print output


def usage():
    print "Usage: %s -i camera ip [-f filename] [-d dirname] [-t timeout] [-n number] [-M movie file] [-m path to mencoder] [-h] [-v]" % (sys.argv[0])
    print "   -i: IP address for camera"
    print "   -f: Filename to use as base [default: webcam]"
    print "   -d: Directory to use [default: .]"
    print "   -t: Timeout to use in seconds [default: 1]"
    print "   -n: Number of images to grab [default: 1]"
    print "   -m: Path to mencoder binary [default: /usr/bin/mencoder]"
    print "   -M: Create a movie to file"
    print "   -v: Verbose"
    print "   -h: Print help"


if __name__ == "__main__":

    timeout = 1
    numimages = 1
    filebase = "webcam"
    directory = "."
    verbose = False
    mencoder = False
    movie = False
    image_list = []
    ip_address = False

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'i:f:d:t:n:m:M:hv')
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

    if '-f' in opts:
        newbase = opts['-f']
        if newbase.endswith('.jpg'):
            newbase = newbase[:-4]
        filebase = newbase

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

    if '-m' in opts:
        if os.path.isfile(opts['-m']) and os.access(opts['-m'], os.X_OK):
            mencoder = opts['-m']
        else:
            print "ERROR: Mencoder binary not found in location %s" % (opts['-m'])

    if '-n' in opts:
        try:
            newnumimages = int(opts['-n'])
        except:
            usage()
            sys.exit(-1)
        numimages = newnumimages

    if '-M' in opts:
        movie = opts['-M']
        if os.path.isfile(movie):
            print "WARNING: Movie %s already exists, hope this is OK" % (movie)

    if os.path.isfile('/usr/bin/mencoder') and os.access('/usr/bin/mencoder', os.X_OK):
        mencoder = '/usr/bin/mencoder'

    if movie and not mencoder:
        print "WARNING: No mencoder found, won't create a movie"

    print "Starting webcam grab, using directory %s, filebase %s, timeout %d, number of images %d" % (directory, filebase, timeout, numimages)
    if movie and mencoder:
        print "Will also make a time lapse in location %s using %s" % (movie, mencoder)
    print "Use Control-C to stop"

    signal.signal(signal.SIGINT, signal_handler)

    image_list = grab_images(ip, directory, filebase, timeout, numimages, verbose)
    if movie and mencoder:
        make_movie(image_list, movie, mencoder, verbose)
