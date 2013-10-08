#!/usr/bin/env python

'''
Assemble - Make a movie from webcam images
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
import re
import os
import getopt

# Approximate file size, below which it's dark
day_night_boundary = 15000
# Number of frames to skip when it's dark
night_frame_skip = 1500


def find_images(directory, ip, verbose=False):
    image_list = []
    image_list_prefilter = []
    numnight = 0

    cameras = os.listdir(directory)
    for camera in cameras:
        if camera != ip:
            if verbose:
                print "Skipping camera %s" % (camera)
            continue
        years = os.listdir(os.path.join(directory, camera))
        for year in years:
            months = os.listdir(os.path.join(directory, camera, year))
            for month in months:
                days = os.listdir(os.path.join(directory, camera, year, month))
                for day in days:
                    hours = os.listdir(os.path.join(directory, camera, year, month, day))
                    for hour in hours:
                        captures = os.listdir(os.path.join(directory, camera, year, month, day, hour))
                        for capture in captures:
                            size = os.path.getsize(os.path.join(directory, camera, year, month, day, hour, capture))
                            num = re.findall('webcam-([0-9.]*).jpg', capture)[0]
                            image_list_prefilter.append((num, size, os.path.join(directory, camera, year, month, day, hour, capture)))

    for (epoch, size, file) in sorted(image_list_prefilter):
        if size > day_night_boundary:
            image_list.append(file)
            numnight = 0
        else:
            if numnight == 0:
                image_list.append(file)
                numnight += 1
            elif numnight == night_frame_skip:
                numnight = 0

    return image_list


def usage():
    print "Usage: %s -i camera ip [-d dirname] [-M movie file] [-m path to mencoder] [-h] [-v]" % (sys.argv[0])
    print "   -i: IP address for camera"
    print "   -d: Directory to use [default: cameras]"
    print "   -m: Path to mencoder binary [default: /usr/bin/mencoder]"
    print "   -M: Create a movie to file"
    print "   -v: Verbose"
    print "   -h: Print help"


if __name__ == "__main__":

    directory = "cameras"
    verbose = False
    mencoder = False
    movie = False
    ip = False

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'd:m:M:i:hv')
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
    else:
        usage()
        sys.exit(-1)

    if '-d' in opts:
        newdir = opts['-d']
        if not os.path.isdir(newdir):
            print "ERROR: Directory %s doesn't exist" % (newdir)
            sys.exit(-1)
        directory = newdir

    if '-m' in opts:
        if os.path.isfile(opts['-m']) and os.access(opts['-m'], os.X_OK):
            mencoder = opts['-m']
        else:
            print "ERROR: Mencoder binary not found in location %s" % (opts['-m'])

    if '-M' in opts:
        movie = opts['-M']
        if os.path.isfile(movie):
            print "WARNING: Movie %s already exists, hope this is OK" % (movie)

    if os.path.isfile('/usr/bin/mencoder') and os.access('/usr/bin/mencoder', os.X_OK):
        mencoder = '/usr/bin/mencoder'

    if movie and not mencoder:
        print "ERROR: No mencoder found, won't create a movie"
        sys.exit(-1)

    image_list = find_images(directory, ip, verbose)

    if movie and mencoder:
        webgrab.make_movie(image_list, movie, mencoder, verbose)
