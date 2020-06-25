#!/usr/bin/env python
# encoding: utf-8

# downloads audio files from Internet Archive collection and create a .m4b audiobook
# Inspired by a code of Robin Camille Davis, Robert Orr and Benjamin Elbers

# Requires: ffmpeg, MP4Box, mp4chaps, mutagen, libmad, mp3wrap

# brew install ffmpeg
# brew install gpac
# brew install mp4chaps
# brew install mp4v2
# brew install libmad
# brew install mp3wrap
# pip install mutagen
# ?? brew install mutagen-io/mutagen/mutagen


import os
import time
import sys
import shutil
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
import signal

output_dir = "output"

bitrate = '128'

search_condition = ""
items = {}

search_max_items = 25
item_number = None
item = None

def signal_handler(sig, frame):
    print('\nCtrl+C has been pressed. Exiting...')
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)    

def secs_to_hms(seconds):
    h, m, s, ms = 0, 0, 0, 0

    if "." in str(seconds):
        splitted = str(seconds).split(".")
        seconds = int(splitted[0])
        ms = int(splitted[1])

    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)

    ms = str(ms)
    try:
        ms = ms[0:3]
    except:
        pass

    return "%.2i:%.2i:%.2i.%s" % (h, m, s, ms)

def hms_to_sec(hms_string):
    seconds= 0
    for part in str(hms_string).split(':'):
        seconds= seconds*60 + float(part)
    return seconds

while True:
    try:
        search_condition = input("Enter search condition or 'x' to exit: ")
    except EOFError as e:
        search_condition = ''

    if (search_condition == 'x' or search_condition == 'X'):
        print("Bye")
        exit(0)
    if (len(search_condition) < 4):
        print("The search condition '{}' is too short".format(search_condition))
        continue

    # Don't forget to run 'ia configure' in your terminal before first start
    search = ia.search_items("title:('{}') AND mediatype:(audio)".format(search_condition))

    if (search.num_found == 0):
        print("Nothing found.\nTry to clarify the search condition")
        continue

    if (search.num_found > search_max_items):
        print("{} items found. It's too many.\nTry to clarify the search condition".format(
            search.num_found))
        continue

    print("{} items found:".format(search.num_found))
    print("===============================================================")

    num = 0
    for result in search:  # for all items
        num = num + 1  # item count
        item_id = result['identifier']
        item = ia.get_item(item_id)
        item_title = item.item_metadata['metadata']['title']
        if (item.metadata.get('access-restricted-item')):
            restricted = 'Restricted'
        else:
            restricted = ''
    
        number_of_files = 0
        total_size = 0
        total_length = 0
        mp3_files = []
        album_covers = []
        if (item.item_metadata['metadata'].get('title')):
            album_title = item.item_metadata['metadata']['title']
        else:
            album_title = ''
        if (item.item_metadata['metadata'].get('artist')):    
            album_artist = item.item_metadata['metadata']['artist']
        elif (item.item_metadata['metadata'].get('creator')):    
            album_artist = item.item_metadata['metadata']['creator']
        else: 
            album_artist = ''

        # collect meta info for each file
        for file in item.files:
            if (file['format'] == 'VBR MP3' or file['format'] == 'MP3'):
                number_of_files = number_of_files + 1
                total_size = total_size + float(file['size'])
                total_length = total_length + hms_to_sec(file['length']) 
                mp3_files.append(file['name'])
            elif (file['format'] == 'JPEG' or file['format'] == 'JPEG Thumb'):
                album_covers.append(file['name'])
            if (file.get('album') and album_title == ''):
                album_title = file['album']
            if (file.get('artist') and album_artist == ''):
                album_artist = file['artist']
                            
        # convert duration and size to human frendly format
        total_length = secs_to_hms(total_length).split('.')[0]
        total_size = humanfriendly.format_size(total_size)

        items[num] = {}
        items[num]['item'] = item
        items[num]['total_length'] = total_length
        items[num]['total_size'] = total_size
        items[num]['number_of_files'] = number_of_files
        items[num]['mp3_files'] = mp3_files
        items[num]['album_covers'] = album_covers
        items[num]['album_title'] = album_title
        items[num]['album_artist'] = album_artist

        print("{}:\t{} ({} file(s), duration: {}, size: {})".format(
            num, item_title, number_of_files, total_length, total_size))

    while True:
        try:
            item_number = input("Enter item number for download, 's' for new search or 'x' to exit: ")
        except EOFError as e:
            item_number = ''
        
        if (item_number == 'x' or item_number == 'X'):
            print("Bye")
            exit(0)    
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

# fetch the item metadata
item_number = int(item_number)
item = items[item_number]['item']
item_id = item.identifier
mp3_files = items[item_number]['mp3_files']
album_covers = items[item_number]['album_covers'] 
album_description = item.item_metadata['metadata']['description']
number_of_files = items[item_number]['number_of_files']
total_length = items[item_number]['total_length']
album_title = items[item_number]['album_title']
album_artist = items[item_number]['album_artist']
if (album_artist == ''):
    album_artist = 'Internet Archive'

print("\n")
album_title = album_title.replace(' - Single Episodes', '')

try:
    album_title = input("Audiobook Name [{}]: ".format(album_title)) or album_title
except EOFError as e:
    None
try:
    album_artist = input("Audiobook Author [{}]: ".format(album_artist)) or album_artist
except EOFError as e:
    None

print("\n\nDownloading item #{}:\t{} ({} files)".format(
    item_number, item_title, number_of_files))

# clean/create output dir
if (os.path.exists(output_dir)):
    shutil.rmtree(output_dir)
os.mkdir(output_dir)
os.chdir(output_dir)

try:
    ia.download(item_id, verbose=True, formats=['VBR MP3', 'MP3', 'JPEG', 'JPEG Thumb'])
    print("Download success.\n\n")
except HTTPError as e:
    if e.response.status_code == 403:
        print("Access to this file is restricted.\nExiting")
except Exception as e:
    print("Error Occurred downloading {}.\nExiting".format(e))

# go to download dir
os.chdir(item_id)

# album_covers.sort()
# mp3_files.sort()

# wrap mp3
subprocess.call(["mp3wrap"] + ["../output.mp3"] + mp3_files)

# convert to aac
print("\nConverting MP3 to audiobook format...\nEstimated duration of the book: {}".format(total_length))
ffmpeg = 'ffmpeg -loglevel fatal -stats -i ../output_MP3WRAP.mp3 -y -vn -acodec aac -ab 128k -ar 44100 -f mp4 ../output.aac'
subprocess.call(ffmpeg.split(" "))

# create chapters file
chapters_file = open('../chapters', 'w')

counter = 0
time = 0

for filename in mp3_files:
    audio = MP3(filename, ID3=EasyID3)
    try:
        title = audio["title"][0]
    except:
        title = filename.replace('.mp3', '')
    audio_file = audioread.audio_open(filename)
    length = audio_file.duration

    counter += 1

    chapters_file.write("CHAPTER%i=%s\n" % (counter, secs_to_hms(time)))
    chapters_file.write("CHAPTER%iNAME=%s\n" % (counter, title))

    time += length

chapters_file.close()

os.chdir("..")

# # add chapters
subprocess.call(["MP4Box", "-add", "output.aac",
                 "-chap", "chapters", "output.mp4"])

# convert chapters to quicktime format
subprocess.call(["mp4chaps", "--convert", "--chapter-qt", "output.mp4"])

# create tags, rename file
audio = MP4("output.mp4")
audio["\xa9nam"] = [album_title]
audio["\xa9ART"] = [album_artist]
audio["desc"] = [album_description]

# Find album cover
if (len(album_covers) == 0):
    print("No cover image found for this item. Using default IA logo.")
    album_covers.append('../../IA_logo.jpg')

# find biggest image
album_cover = ''
max_cover_size = 0
for cover in album_covers:
    cover_size = os.path.getsize(os.path.join(item_id, cover))
    if (cover_size >= max_cover_size):
        max_cover_size = cover_size
        album_cover = cover

# add album cover to the audiobook
image_type = 13
data = open(os.path.join(item_id, album_cover), 'rb').read()
audio["covr"] = [MP4Cover(data, image_type)]

audio.save()

os.rename("output.mp4", "%s - %s.m4b" % (album_artist, album_title))

# clean up
shutil.rmtree(item_id)
os.remove("chapters")
os.remove("output.aac")
os.remove("output_MP3WRAP.mp3")

os.chdir("..")
