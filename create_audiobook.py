#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is in the Public Domain.
# Copyright (C) 2010 Benjamin Elbers <elbersb@gmail.com>
# 
# Takes all mp3 files in the current directory and creates a properly tagged
# audio book (m4b) with chapter marks in the "output" directory.
#
# Note: The mp3 files should have proper ID3 tags. The "title" tag of each mp3
#       file is used as the corresponding chapter title. The "artist" and 
#       "album" tags of the first file are used as tags for the complete 
#       audio book.
# Note: To have the chapters in the correct order, the filenames have to be
#       sortable (e.g. "01 - First chapter.mp3", "02 - Second chapter.mp3"). 
# Note: To make the chapter marks show up on the iPod use gtkPod>=v0.99.14 or
#       iTunes for transferring the audio book.
#
# Requires: ffmpeg, MP4Box, mp4chaps, mutagen, libmad, mp3wrap

# brew install ffmpeg
# brew install gpac
# brew install mp4chaps
# brew install mp4v2
# pip install mutagen
# ?? brew install mutagen-io/mutagen/mutagen
# brew install libmad
# brew install mp3wrap


from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4
from mutagen.mp4 import MP4Cover
import audioread
import time
import os
import subprocess

input_dir = "OTRR_Box_13_Singles"
artist = "Dan Holiday"
album_title = "Box 13"


output_dir = "output"


bitrate = '128'

# go to input dir
os.chdir(input_dir)

# create output dir
if (os.path.exists(output_dir)):
    for i in os.listdir(output_dir):
        os.remove(os.path.join(output_dir, i))
    os.rmdir(output_dir)
os.mkdir(output_dir)

# check for cover file
album_covers = [filename for filename in os.listdir(".") if filename.endswith(('.jpg', '.jpeg', '.png'))]
album_covers.sort()

# get mp3
mp3_files = [filename for filename in os.listdir(".") if filename.endswith(".mp3")]
mp3_files.sort()

# wrap mp3
subprocess.call(["mp3wrap"] + ["output/output.mp3"] + mp3_files)

# convert to aac
ffmpeg = 'ffmpeg -i output/output_MP3WRAP.mp3 -y -vn -acodec aac -ab 128k -ar 44100 -f mp4 output/output.aac'
subprocess.call(ffmpeg.split(" "))

# create chapters file
def secs_to_hms(seconds):
    h, m, s, ms = 0, 0, 0, 0

    if "." in str(seconds):
        splitted = str(seconds).split(".")
        seconds = int(splitted[0])
        ms = int(splitted[1])

    m,s = divmod(seconds,60)
    h,m = divmod(m,60)       


    ms = str(ms)
    try:
        ms = ms[0:3]
    except:
        pass   

    return "%.2i:%.2i:%.2i.%s" % (h, m, s, ms)

chapters_file = open('output/chapters', 'w')

counter = 0
time = 0

for filename in mp3_files:
    audio = MP3(filename, ID3=EasyID3)
    title = audio["title"][0]
    audio = MP3(filename, ID3=EasyID3)
    title = audio["title"][0]
    audio_file = audioread.audio_open(filename)
    length = audio_file.duration

    if not artist:
        artist = audio["artist"][0]
        album_title = audio["album"][0]

    counter += 1

    chapters_file.write("CHAPTER%i=%s\n" % (counter, secs_to_hms(time)))
    chapters_file.write("CHAPTER%iNAME=%s\n" % (counter, title))

    time += length

chapters_file.close()

os.chdir("output")

# add chapters
subprocess.call(["MP4Box", "-add", "output.aac", "-chap", "chapters", "output.mp4"])

# convert chapters to quicktime format
subprocess.call(["mp4chaps", "--convert", "--chapter-qt", "output.mp4"])

# clean up
os.remove("chapters")
os.remove("output.aac")
os.remove("output_MP3WRAP.mp3")

# create tags, rename file
audio = MP4("output.mp4")
audio["\xa9nam"] = [album_title]
audio["\xa9ART"] = [artist]

for cover in album_covers:
    image_type = 13
    if "png" in cover:
        image_type = 14
    data = open("../"+cover, 'rb').read()
    audio["covr"] = [MP4Cover(data, image_type)]

audio.save()

os.rename("output.mp4", "%s - %s.m4b" % (artist, album_title))
