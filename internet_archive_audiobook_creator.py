#!/usr/bin/env python
# encoding: utf-8

## downloads audio files from Internet Archive collection and create a .m4b audiobook
## Inspired by a code of Robin Camille Davis, Robert Orr and Benjamin Elbers

# Requires: ffmpeg, MP4Box, mp4chaps, mutagen, libmad, mp3wrap

# brew install ffmpeg
# brew install gpac
# brew install mp4chaps
# brew install mp4v2
# pip install mutagen
# ?? brew install mutagen-io/mutagen/mutagen
# brew install libmad
# brew install mp3wrap


import os
import time
import sys
import internetarchive as ia
from requests.exceptions import HTTPError
from datetime import timedelta
import humanfriendly
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4
from mutagen.mp4 import MP4Cover
import audioread
import subprocess

input_dir = "input"
output_dir = "output"

bitrate = '128'

search_condition = ""
items = {}
search_max_items = 10
item_number = None
item = None

while True:
    search_condition = input("Enter search condition or 'x' to exit: ")
    if (search_condition == 'x'):
        print("Bye")
        exit(0)
    if (len(search_condition) < 4):
        print("The search condition '{}' is too short".format(search_condition))
        continue

    # Don't forget to run 'ia configure' in your terminal before first start
    search = ia.search_items("title:('{}') AND mediatype:(audio)".format(search_condition))

    if (search.num_found == 0 or search.num_found > search_max_items):
        print("{} items found. It's too many.\nTry to clarify the search condition".format(search.num_found))
        continue

    print("{} items found:".format(search.num_found))
    print("===============================================================")

    num = 0
    for result in search: # for all items 
        num = num + 1 # item count
        item_id = result['identifier']
        item = ia.get_item(item_id)
        items[num] = item
        title = item.item_metadata['metadata']['title']
        restricted = ''
        try:
            restricted = 'Restricted' if item.metadata['access-restricted-item'] else '' 
        except Exception as ex:
            restricted = ''
        number_of_files = 0
        total_size = 0
        total_length = 0
        for file in item.files:
            if ('MP3' in file['format'].upper()):
                number_of_files = number_of_files + 1
                total_size = total_size + float(file['size'])
                total_length = total_length + float(file['length'])

        total_length = str(timedelta(seconds=int(total_length)))
        total_size = humanfriendly.format_size(total_size)
        print("{}:\t{} ({} file(s), length: {}, size: {})".format(num, title, number_of_files, total_length, total_size))

    while True:
        item_number = input("Enter item number for download or 's' for new search: ")
        if (item_number == 's' or item_number == 'S'):
            item_number = None
            break
        if (not item_number.isnumeric() or int(item_number) < 1 or int(item_number) > len(items)):
            print("Invalid item number")
            continue
        else:
            break

    if (item_number == None):
        continue
    else:
        break        
    
item_number = int(item_number)
item = items[item_number]
item_id = item.identifier
title = item.item_metadata['metadata']['title']
try:
    artist = item.item_metadata['metadata']['artist']
except Exception as e:
    artist = 'Unknown Artist'

print("\n\nDownloading item #{}:\t{} ({} files)".format(item_number, title, item.files_count))

# clean/create input dir
if (os.path.exists(input_dir)):
    for i in os.listdir(input_dir):
        os.remove(os.path.join(input_dir, i))
    os.rmdir(input_dir)
os.mkdir(input_dir)

# clean/create output dir
if (os.path.exists(output_dir)):
    for i in os.listdir(output_dir):
        os.remove(os.path.join(output_dir, i))
    os.rmdir(output_dir)
os.mkdir(output_dir)

# go to input dir
os.chdir(input_dir)

try:
    ia.download(item_id, verbose=True, glob_pattern='*.mp3|*.jpg')
    print("Download success.\n\n")
except HTTPError as e:
    if e.response.status_code == 403:
     print("Access to this file is restricted.\nExiting")     
except Exception as e:
    print("Error Occurred downloading {}.\nExiting".format(e)) 

# go to download dir
os.chdir(item_id)

# check for cover file
album_covers = [filename for filename in os.listdir(".") if filename.endswith(('.jpg', '.jpeg', '.png'))]
album_covers.sort()

# get mp3
mp3_files = [filename for filename in os.listdir(".") if filename.endswith(".mp3")]
mp3_files.sort()

# wrap mp3
subprocess.call(["mp3wrap"] + ["../../output/output.mp3"] + mp3_files)

# convert to aac
ffmpeg = 'ffmpeg -i ../../output/output_MP3WRAP.mp3 -y -vn -acodec aac -ab 128k -ar 44100 -f mp4 ../../output/output.aac'
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

chapters_file = open('../../output/chapters', 'w')

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

os.chdir("../../output")

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
audio["\xa9nam"] = [title]
audio["\xa9ART"] = [artist]

for cover in album_covers:
    image_type = 13
    if "png" in cover:
        image_type = 14
    data = open("../"+cover, 'rb').read()
    audio["covr"] = [MP4Cover(data, image_type)]

audio.save()

os.rename("output.mp4", "%s - %s.m4b" % (artist, title))

os.chdir("..")
