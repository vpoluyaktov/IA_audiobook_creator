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
import subprocess
import signal
import requests
import re
from requests.exceptions import HTTPError
import shutil
import internetarchive as ia
import humanfriendly
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4
from mutagen.mp4 import MP4Cover
import audioread

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
        format_list = ['48Kbps MP3', '64Kbps MP3', '128Kbps MP3', '256Kbps MP3', 'VBR MP3'] # format list ranged by priority 
        for file in item.files:
            if (file['format'] in format_list):
                # check if there is a file with the same title but different bitrate. Keep highest bitrate only
                existing_file_index = 0
                keep_existing_file = False
                if (not 'title' in file):
                    file['title'] = file['name']

                for existing_file in mp3_files:
                    if (file['title'] == existing_file['title']):
                        existing_file_priority = format_list.index(existing_file['format'])
                        new_file_priority = format_list.index(file['format'])
                        if (new_file_priority > existing_file_priority):
                            # remove existing file from the list
                            mp3_files.pop(existing_file_index)  
                        else:
                            keep_existing_file = True
                        break    
                    existing_file_index += 1   
                if (not keep_existing_file):    
                    mp3_files.append({'title': file['title'], 'file_name' : file['name'], 'format': file['format'], 'size': float(file['size']), 'length': hms_to_sec(file['length'])})
            elif (file['format'] in ['JPEG', 'JPEG Thumb']):
                album_covers.append(file['name'])
            elif ('MP3' in file['format']):
                print("Skipping MP3 format: {}".format(file['format']))
            if (file.get('album') and album_title == ''):
                album_title = file['album']
            if (file.get('artist') and album_artist == ''):
                album_artist = file['artist']

        # calculate item total size
        total_size = 0.0                    
        for file in mp3_files:
            total_size += file['size']

        # calculate item total length
        total_length = 0.0                    
        for file in mp3_files:
            total_length += file['length']

        number_of_files = len(mp3_files)    

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
album_title = album_title.replace(album_artist + ' - ', '')

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
# if (os.path.exists(output_dir)):
#     shutil.rmtree(output_dir)
# os.mkdir(output_dir)
os.chdir(output_dir)

# downloading mp3 files
for file in mp3_files:
    file_title = file['title']
    file_name = file['file_name']
    file_size = file['size']
    try:
        print("\t{} ({})...".format(file_title, humanfriendly.format_size(file_size)), end =" ")
        # result = ia.download(item_id, silent=True, files = file_name)
        print("\t\tOK")
    except HTTPError as e:
        if e.response.status_code == 403:
            print("Access to this file is restricted.\nExiting")
    except Exception as e:
        print("Error Occurred downloading {}.\nExiting".format(e))


# downloading images       
for file in album_covers:
    file_name = file   
    try:
        print("\t{}...".format(file_name), end =" ")
        result = ia.download(item_id, silent=True, files = file_name)
        print("\t\tOK")
    except HTTPError as e:
        if e.response.status_code == 403:
            print("Access to this file is restricted.\nExiting")
    except Exception as e:
        print("Error Occurred downloading {}.\nExiting".format(e))


# go to download dir
if (not os.path.exists(item_id)):
    print("Nothing to do. Exiting...")
    exit(1)

os.chdir(item_id)

mp3_file_names = []
for file in mp3_files:
    mp3_file_names.append(file['file_name'])
mp3_file_names.sort()

mp3_list_file = open('mp3_files.txt', 'w')
for file in mp3_file_names:
    mp3_list_file.write("file '{}'\n".format(file))
mp3_list_file.close()

# convert to aac
print("\nConverting MP3 to audiobook format...\nEstimated duration of the book: {}".format(total_length))
ffmpeg = 'ffmpeg -f concat -safe 0 -loglevel fatal -stats -i mp3_files.txt -y -vn -acodec aac -ab 128k -ar 44100 -f mp4 ../output.aac'
subprocess.call(ffmpeg.split(" "))

# create chapters file
chapters_file = open('../chapters', 'w')

counter = 0
time = 0

for filename in mp3_file_names:
    audio = MP3(filename, ID3=EasyID3)
    try:
        title = audio["title"][0]
        title = title.replace(album_title, '').replace('  ', ' ').replace('- -', '-').replace('  ', ' ')
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
    print("\nNo cover image found for this item. Using default IA logo.")
    while (True):
        choice_number = input("You have two options:\n 1) Use default Internet Archive logo\n 2) Use some local picture file\n Your choice: ")

        if (not choice_number.isnumeric() or int(choice_number) < 1 or int(choice_number) > 2):
            print("Invalid choice number")
            continue
        else:
            break

    if (int(choice_number) == 1):
        img_url = "https://archive.org/20/items/InternetArchiveLogo_201805/internet%20archive%20logo.jpg"
        img_name = os.path.basename(img_url)
        try:
            request = requests.get(img_url, allow_redirects=True)
            open(os.path.join(item_id, img_name), 'wb').write(request.content)
            album_covers.append(img_name)
        except Exception as e:
            None
    elif (int(choice_number) == 2):
        while (True):
            local_file_name = input("Enter full path to a picture file (.jpeg or .png): ")
            if (any(re.findall(r'.jpg|.jpeg|.png', local_file_name, re.IGNORECASE)) and  os.path.isfile(local_file_name)):
                break
            else:
                print("Can't opent the file: {}".format(local_file_name))
        album_covers.append(local_file_name)

# find biggest image
album_cover = ''
max_cover_size = 0
for cover in album_covers:
    cover_size = os.path.getsize(os.path.join(item_id, cover))
    if (cover_size >= max_cover_size):
        max_cover_size = cover_size
        album_cover = cover

# add album cover to the audiobook
if ".PNG" in cover.upper():
    image_type = 14
else:
    image_type = 13
data = open(os.path.join(item_id, album_cover), 'rb').read()
audio["covr"] = [MP4Cover(data, image_type)]

audio.save()

audiobook_file_name = "{} - {}.m4b".format(album_artist, album_title)
os.rename("output.mp4", audiobook_file_name)

# clean up
shutil.rmtree(item_id)
os.remove("chapters")
os.remove("output.aac")
# os.remove("output_MP3WRAP.mp3")

os.chdir("..")

print("\nAudiobook created: output/{}\n".format(audiobook_file_name))