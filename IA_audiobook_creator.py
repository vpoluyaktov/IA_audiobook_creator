#!/usr/bin/env python3
# encoding: utf-8

# This script downloads audio files from Internet Archive collection and create a .m4b audiobook
# Inspired by a code of Robin Camille Davis, Robert Orr and Benjamin Elbers

# REQUIREMENTS:
# pip install internetarchive
# pip install humanfriendly
# pip install mutagen
# pip install audioread
# pip install python-magic
# pip install html2text

# Linux (debian/ubuntu)
# sudo apt-get install ffmpeg
# sudo apt-get install internetarchive
# then run:
# ia configure (enter your archive.org username and password)

# MacOS:
# brew install ffmpeg
# brew install internetarchive
# then run:
# ia configure (enter your archive.org username and password)


import os
import math
import sys
import subprocess
import signal
import requests
import re
import chardet
from requests.exceptions import HTTPError
import shutil
import internetarchive as ia
import humanfriendly
import humanfriendly.prompts
import html2text
import magic
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4
from mutagen.mp4 import MP4Cover

archive_org_url = "https://archive.org"
output_dir = "output"

# debug feature-toggles
PRE_CLEANUP = True
CREATE_DIRS = True
DOWNLOAD_IMAGES = True
DOWNLOAD_MP3 = True
RE_ENCODE_MP3 = True
CONCATENATE_MP3 = True
CONVERT_TO_MP4 = True
POST_CLEANUP = False

# Experimental features. Use with caution
FIX_ID3_ENCODING = True
COMBINE_CHAPTER_TITLES = True

BITRATE = "128k"
SAMPLE_RATE = "44100"
BIT_DEPTH = "s16"
OUTPUT_MODE="stereo" # mono / stereo
GAP_DURATION = 5 # Duration of a gaps between chapters
part_size_human = "2 GB" # default audiobook part size

# small adjustment (don't ask me why - just noticed mutagen returns slighly incorrect value)
# if you hear the end of previous chapter at the beginning of new one - slightly increase the value of this parameter
# if new chapter sound starts too early - decrease the value
MP3_DURATION_ADJUSTMENT = -50

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

def get_mp3_title(file_name):
    try:
        mp3 = MP3(file_name , ID3=EasyID3)
        title = mp3["title"][0]
    except:
        title = os.path.basename(file_name).replace('.mp3', '')

    if FIX_ID3_ENCODING:
        # try to repair bad ID3 tags encoding
        try:
            bytes = title.encode('iso-8859-1')
            charset = chardet.detect(bytes)
            if charset['confidence'] > 0.8:
                codepage = charset['encoding']
                if codepage == 'MacCyrillic':
                    codepage = 'windows-1251' # These two code pages are too similar, so let's prefer windows-1251
            else:
                codepage = 'windows-1251' # If not sure - use windows-1251 code page
            title = bytes.decode(codepage)
        except:
            pass

    if COMBINE_CHAPTER_TITLES: # Experimental feature
        reduce_tuples = [(r'^(\d+)$', r'Chapter \1'), (r'(\d+_)+_?', ''), (r'Ôðàãìåíò \d+$', ''), (r'Фрагмент \d+$', ''), (r'\(?[Ч|ч]асть \d+\)?$', '')]
        for tuple in reduce_tuples:
            title = re.sub(tuple[0], tuple[1], title)

    title = title.replace(album_title, '').replace('  ', ' ').replace('- -', '-').replace('  ', ' ').strip()

    return title

def get_mp3_length(file_name):
    try:
        mp3 = MP3(file_name , ID3=EasyID3)
        length = mp3.info.length
    except:
        length = 0
    return length


print("\nInternet Archive audiobook creator script")

while True:
    try:
        search_condition = input("\nEnter search condition or 'x' to exit: ")
    except EOFError as e:
        search_condition = ''

    if (search_condition == 'x' or search_condition == 'X'):
        print("Bye")
        exit(0)
    if (len(search_condition) < 4):
        print("The search condition '{}' is too short".format(search_condition))
        continue

    # Don't forget to run 'ia configure' in your terminal before first start
    search_query = ""
    if (search_condition.find(archive_org_url + "/details/") != -1):
        item_id = search_condition.replace(archive_org_url + "/details/", '').split('/')[0]
        search_query = "identifier:{} AND mediatype:(audio)".format(item_id)
    else:
        search_query = "title:('{}') AND mediatype:(audio)".format(search_condition)
    search = ia.search_items(search_query)

    if (not isinstance(search.num_found, int)):
        print("IA failed to parse your request.\nTry to clarify the search condition")
        continue

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

        if (item.urls.details):
            item_url = item.urls.details
        else:
            item_url = ''
        if (item.item_metadata['metadata'].get('licenseurl')):
            license_url = item.item_metadata['metadata']['licenseurl']
        else:
            license_url = ''

        # collect meta info for each file
        format_list = ['16Kbps MP3', '24Kbps MP3', '32Kbps MP3', '40Kbps MP3', '48Kbps MP3', '56Kbps MP3', '64Kbps MP3', '80Kbps MP3', '96Kbps MP3', '112Kbps MP3', '128Kbps MP3', '144Kbps MP3', '160Kbps MP3', '224Kbps MP3', '256Kbps MP3', '320Kbps MP3', 'VBR MP3'] # format list ranged by priority
        for file in item.files:
            if (file['format'] in format_list):
                # check if there is a file with the same title but different bitrate. Keep highest bitrate only
                existing_file_index = 0
                add_new_file = True
                if (not 'title' in file):
                    file['title'] = file['name']

                for existing_file in mp3_files:
                    if (file['title'] == existing_file['title']):
                        existing_file_priority = format_list.index(existing_file['format'])
                        new_file_priority = format_list.index(file['format'])
                        if (new_file_priority > existing_file_priority):
                            # remove existing file from the list
                            mp3_files.pop(existing_file_index)
                            add_new_file = True
                        elif (new_file_priority == existing_file_priority):
                            # most likely many files have the same title
                            add_new_file = True
                        else:
                            add_new_file = False
                        break
                    existing_file_index += 1
                if add_new_file:
                    mp3_files.append({'title': file['title'], 'file_name' : file['name'], 'format': file['format'], 'size': float(file['size']), 'length': hms_to_sec(file['length'])})
            elif (file['format'] in ['JPEG', 'JPEG Thumb']):
                album_covers.append(file['name'])
            elif ('MP3' in file['format']):
                None # print("Skipping unknown MP3 format: {}".format(file['format']))
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
        total_length_human = secs_to_hms(total_length).split('.')[0]
        total_size_human = humanfriendly.format_size(total_size)

        items[num] = {}
        items[num]['item'] = item
        items[num]['item_title'] = item_title
        items[num]['total_length'] = total_length
        items[num]['total_length_human'] = total_length_human
        items[num]['total_size'] = total_size
        items[num]['total_size_human'] = total_size_human
        items[num]['number_of_files'] = number_of_files
        items[num]['mp3_files'] = mp3_files
        items[num]['album_covers'] = album_covers
        items[num]['album_title'] = album_title
        items[num]['album_artist'] = album_artist
        items[num]['item_url'] = item_url
        items[num]['license_url'] = license_url

        print("{}:\t{} ({} file(s), duration: {}, size: {})".format(
            num, item_title, number_of_files, total_length_human, total_size_human))

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
item_title = items[item_number]['item_title']
item = items[item_number]['item']
item_id = item.identifier
mp3_files = items[item_number]['mp3_files']
album_covers = items[item_number]['album_covers']
number_of_files = items[item_number]['number_of_files']
total_length = items[item_number]['total_length']
total_length_human = items[item_number]['total_length_human']
total_size = items[item_number]['total_size']
total_size_human = items[item_number]['total_size_human']
album_title = items[item_number]['album_title']
item_url = items[item_number]['item_url']
license_url = items[item_number]['license_url']

# convert html description to plain text
album_description = item.item_metadata['metadata']['description']
parser = html2text.HTML2Text()
parser.ignore_links = True
parser.ignore_emphasis = True
parser.single_line_brake = True
parser.ignore_tables = True
album_description = parser.handle(album_description)

# remove block quotes and extra empty lines from the album description
while True:
    album_description_original = album_description
    album_description = re.sub('^> ', '',album_description)
    album_description = re.sub('\n> ', '\n',album_description)
    album_description = re.sub('\n>\n|\n\s*\n', '\n\n',album_description)
    album_description = re.sub('\n\n\n', '\n\n',album_description)
    if album_description_original == album_description:
        break

# confirm audiobook title and author
album_artist = items[item_number]['album_artist']
if (album_artist == ''):
    album_artist = 'Internet Archive'
album_title = album_title.replace(' - Single Episodes', '')
album_title = album_title.replace(album_artist + ' - ', '')
album_artist = album_artist.replace('Old Time Radio Researchers Group', 'OTRR')
try:
    album_title = input("\nAudiobook Name [{}]: ".format(album_title)) or album_title
except EOFError as e:
    None
try:
    album_artist = input("Audiobook Author [{}]: ".format(album_artist)) or album_artist
except EOFError as e:
    None

# check if audiobook size is bigger than default part size and ask a user to adjust if needed
part_size = humanfriendly.parse_size(part_size_human)
if (total_size > part_size):
    while True:
        try:
            number_of_parts = math.ceil(total_size / part_size)
            print("\nThe audiobook total size ({}) is bigger than default single part size ({}), so the book will be split into {} parts."
                .format(total_size_human, part_size_human, number_of_parts))
            if (humanfriendly.prompts.prompt_for_confirmation("Would you like to change default part size?", default=False)):
                part_size_human = input("Enter new part size (Mb, Gb): ")
                part_size = humanfriendly.parse_size(part_size_human)
                part_size_human = humanfriendly.format_size(part_size) # reformat user input
            else:
                break
        except humanfriendly.InvalidSize as e:
            print("ERROR: Wrong size specified. You can say for ex: 2 Gb, 0.5 Gb, 256 Mb, etc.")

EDIT_CHAPTER_NAMES=False
if (humanfriendly.prompts.prompt_for_confirmation("\nWould you like to edit chapter names at the end of the book creation?", default=False)):
    EDIT_CHAPTER_NAMES=True

print("\n\nDownloading item #{}:\t{} ({} files)".format(
    item_number, item_title, number_of_files))

# clean/create output dir
if PRE_CLEANUP:
    if (os.path.exists(output_dir)):
        shutil.rmtree(output_dir)
if CREATE_DIRS:
    os.makedirs(os.path.join(output_dir, item_id))
os.chdir(output_dir)

# downloading images
print("\nDownloading album covers")
for file in album_covers:
    file_name = file
    try:
        print("    {:90}".format(file_name + "..."), end =" ", flush=True)
        if DOWNLOAD_IMAGES:
            result = ia.download(item_id, silent=True, files = file_name)
        print("OK")
    except HTTPError as e:
        if e.response.status_code == 403:
            print("Access to this file is restricted.\nExiting")
    except Exception as e:
        print("Error Occurred downloading {}.\nExiting".format(e))

# find biggest cover image
album_cover = ''
max_cover_size = 0
for cover in album_covers:
    cover_size = os.path.getsize(os.path.join(item_id, cover))
    if (cover_size >= max_cover_size):
        max_cover_size = cover_size
        album_cover = cover

# Check if the audiobook has album cover
if len(album_covers) == 0 or (len(album_covers) == 1 and album_covers[0] == '__ia_thumb.jpg'):
    print("No cover image found for this item.")
    while (True):
        choice_number = input("You have three options:\n 1) Use default Internet Archive logo\n 2) Use an image from Internet\n 3) Use local picture file\n Your choice: ")

        if (not choice_number.isnumeric() or int(choice_number) < 1 or int(choice_number) > 3):
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
            album_cover = img_name
        except Exception as e:
            None
    elif (int(choice_number) == 2):
        while (True):
            img_url = input("Enter a picture url (.jpeg or .png format): ")
            img_name = os.path.basename(img_url)
            try:
                request = requests.get(img_url, allow_redirects=True)
                open(os.path.join(item_id, img_name), 'wb').write(request.content)

                # check if downloaded file is valid .jpeg or .png image
                if (
                    any(re.findall(r'.jpg|.jpeg|.png', img_name, re.IGNORECASE))
                    and  os.path.isfile(os.path.join(item_id, img_name))
                    and (
                        magic.from_file(os.path.join(item_id, img_name), mime=True) == 'image/jpeg'
                        or magic.from_file(os.path.join(item_id, img_name), mime=True) == 'image/png'
                        )
                    ):
                    album_cover = img_name
                    break
                else:
                    print("The file is not an .jpeg or .png image: {}".format(img_name))
            except Exception as e:
                print("Can't download the picture file: {}".format(e))
    elif (int(choice_number) == 3):
        while (True):
            local_file_name = input("Enter full path to a picture file (.jpeg or .png format): ")
            if (any(re.findall(r'.jpg|.jpeg|.png', local_file_name, re.IGNORECASE)) and  os.path.isfile(local_file_name)):
                break
            else:
                print("Can't opent the file: {}".format(local_file_name))
        album_cover = local_file_name

# downloading mp3 files
print("\nDownloading mp3 files")
file_number = 1
for file in mp3_files:
    file_title = file['title']
    file_name = file['file_name']
    file_size = file['size']
    try:
        print("{:6d}/{}: {:83}".format(file_number, len(mp3_files), file_name + ' (' + humanfriendly.format_size(file_size) + ")..."), end = " ", flush=True)
        if DOWNLOAD_MP3:
            result = ia.download(item_id, silent=True, files = file_name)
        print("OK")
        file_number += 1
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
if CREATE_DIRS:
    os.mkdir('resampled')

mp3_file_names = []
for file in mp3_files:
    mp3_file_names.append(file['file_name'])
# mp3_file_names.sort()

# generated silence .mp3 to fill gaps between chapters
os.system('ffmpeg -nostdin -f lavfi -i anullsrc=r={}:cl={} -t {} -hide_banner -loglevel fatal -nostats -y -ab {} -ar {} -vn "resampled/gap.mp3"'.format(SAMPLE_RATE, OUTPUT_MODE, GAP_DURATION, BITRATE, SAMPLE_RATE))
os.system('ffmpeg -nostdin -f lavfi -i anullsrc=r={}:cl={} -t {} -hide_banner -loglevel fatal -nostats -y -ab {} -ar {} -vn "resampled/half_of_gap.mp3"'.format(SAMPLE_RATE, OUTPUT_MODE, GAP_DURATION / 2, BITRATE, SAMPLE_RATE))

# adjust GAP_DURATION because ffmpeg doesn't produce exact mp3 length
GAP_DURATION = get_mp3_length("resampled/gap.mp3")

print("\nRe-encoding .mp3 files all to the same bitrate and sample rate...")
file_number = 1
for file_name in mp3_file_names:
    if os.path.dirname(file_name) and not os.path.exists(os.path.join('resampled', os.path.dirname(file_name))):
        os.makedirs(os.path.join('resampled', os.path.dirname(file_name))) # create dir structure for complex file names
    print("{:6d}/{}: {:67}".format(file_number, len(mp3_file_names), file_name + '...'), end = " ", flush=True)
    if RE_ENCODE_MP3:
        os.system('ffmpeg -nostdin -i "{}" -hide_banner -loglevel fatal -nostats -y -ab {} -ar {} -vn "resampled/{}"'.format(file_name, BITRATE, SAMPLE_RATE, file_name))
    print("OK")
    file_number += 1

# recalculate total audiobook size, split the books on parts if needed
total_size = 0
current_part_size = 0
file_number = 1
part_number = 1
audiobook_parts = {}
part_audio_files = []

for file_name in mp3_file_names:
    # check if the filename is "safe" (see ffmpeg doc) and fix it if needed
    unsafe_tuples = [('...', '.'), ('..', '.')]
    unsafe_file_name = file_name
    intermediate_file_name = unsafe_file_name
    for tuple in unsafe_tuples:
        intermediate_file_name = intermediate_file_name.replace(tuple[0], tuple[1])
    safe_file_name = intermediate_file_name
    if unsafe_file_name != safe_file_name:
        # rename file (create new dir if needed)
        dir_name = os.path.join('resampled', os.path.dirname(safe_file_name))
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
        os.rename('resampled/' + unsafe_file_name, 'resampled/' + safe_file_name)
        file_name = safe_file_name

    part_audio_files.append(file_name)
    file_size = os.stat("resampled/{}".format(file_name)).st_size
    current_part_size += file_size
    total_size += file_size

    if file_number == len(mp3_file_names) or current_part_size >= part_size:
        # we have collected enought files for the audiobook part.
        audiobook_parts[part_number] = {}
        audiobook_parts[part_number]['mp3_file_names'] = part_audio_files
        audiobook_parts[part_number]['part_size'] = current_part_size

        part_number += 1
        current_part_size = 0
        part_audio_files = []
    file_number += 1

number_of_parts = math.ceil(total_size / part_size)
if number_of_parts > 1:
    total_size_human = humanfriendly.format_size(total_size)
    print("\nAdjusted audiobook total size is {}. The book will be split into {} parts.".format(total_size_human, number_of_parts))

# create a chapter files and audio files list for each part
print("\nCreating audiobook chapters")
part_number = 1
chapter_number = 1
for audiobook_part in audiobook_parts:
    if len(audiobook_parts) > 1:
        print("\n{}. Part {}".format(album_title, part_number))
        print("---------------------------------------------------------")

    mp3_list_file_name = "../audio_files.part{:0>3}".format(part_number)
    audiobook_parts[part_number]['mp3_list_file_name'] = mp3_list_file_name
    mp3_list_file = open(mp3_list_file_name, 'w')
    mp3_list_file.write("file 'resampled/half_of_gap.mp3'\n")

    chapters_file_name = "../chapters.part{:0>3}".format(part_number)
    audiobook_parts[part_number]['chapters_file_name'] = chapters_file_name
    chapters_file = open(chapters_file_name, 'w')

    chapters_file.write(";FFMETADATA1\n")
    chapters_file.write("major_brand=isom\n")
    chapters_file.write("minor_version=1\n")
    chapters_file.write("compatible_brands=isom\n")
    chapters_file.write("encoder=Lavf58.20.100\n")

    #chapter_number = 1
    file_number = 1
    chapter_start_time = 0
    chapter_end_time = 0
    chapter_length = 0
    total_part_size = 0
    total_part_length = 0
    part_audio_files = audiobook_parts[part_number]['mp3_file_names']

    # brake files into chapters
    for filename in part_audio_files:
        mp3_title = get_mp3_title(filename)
        if not mp3_title:
            mp3_title = "Chapter {}".format(chapter_number)
        length = get_mp3_length('resampled/' + filename) + (MP3_DURATION_ADJUSTMENT / 1000)
        chapter_end_time = chapter_end_time + length
        file_size = os.stat("resampled/{}".format(filename)).st_size
        mp3_list_file.write("file 'resampled/{}'\n".format(filename.replace("'","'\\''")))
        total_part_size += file_size
        chapter_length += length
        total_part_length += length

        # if this is last file in the list or next file title is different from current one - finish the chapter
        if file_number == len(part_audio_files) \
            or mp3_title != get_mp3_title(part_audio_files[file_number]): # next file title
            # chapter changed
            chapter_title = mp3_title

            mp3_list_file.write("file 'resampled/gap.mp3'\n")
            chapter_end_time += GAP_DURATION + (MP3_DURATION_ADJUSTMENT / 1000)
            chapters_file.write("[CHAPTER]\n")
            chapters_file.write("TIMEBASE=1/1000\n")
            chapters_file.write("START={}\n".format(int(chapter_start_time * 1000)))
            chapters_file.write("END={}\n".format(int(chapter_end_time * 1000)))
            chapters_file.write("title={}\n".format(chapter_title))
            print("Chapter {:>3} ({}): {}".format(chapter_number, secs_to_hms(chapter_length).split('.')[0], chapter_title))
            chapter_length = 0
            chapter_start_time = chapter_end_time
            chapter_number += 1

        file_number += 1

    chapters_file.close()
    mp3_list_file.write("file 'resampled/half_of_gap.mp3'\n")
    mp3_list_file.close()
    if len(audiobook_parts) > 1:
        print("---------------------------------------------------------")
        print("Part size: {}. Part length: {}".format( humanfriendly.format_size(total_part_size), secs_to_hms(total_part_length)))
    audiobook_parts[part_number]['chapters_file_name'] = chapters_file_name
    audiobook_parts[part_number]['part_length'] = total_part_length
    part_number += 1

if EDIT_CHAPTER_NAMES:
    print("\nNow you can edit chapter names. \nOpen the folowing file(s) in any text editor:")
    part_number = 1
    for audiobook_part in audiobook_parts:
        print("\t{}".format(os.path.abspath(audiobook_parts[part_number]['chapters_file_name'])))
        part_number += 1
    input("\nPress <Enter> when you are done...")

# concatenate .mp3 files into big .mp3 and attach chapter meta info
part_number = 1
for audiobook_part in audiobook_parts:
    if len(audiobook_parts) > 1:
        print("\nProcessing Part {} from {}".format(part_number, number_of_parts))
        print("---------------------------------------------------------")
        print("Combining .mp3 files into big one...\nEstimated duration of the part: {}".format(secs_to_hms(audiobook_parts[part_number]['part_length'])))
    else:
        print("\nCombining single .mp3 files into big one...\nEstimated duration of the book: {}".format(secs_to_hms(audiobook_parts[part_number]['part_length'])))
    if CONCATENATE_MP3:
        command = "ffmpeg -nostdin -f concat -safe 0 -loglevel fatal -stats -i {} -y -vn -ab {} -ar {} -acodec aac ../output.part{:0>3}.aac".format(audiobook_parts[part_number]['mp3_list_file_name'],BITRATE, SAMPLE_RATE, part_number)
        subprocess.call(command.split(" "))

    print("\nConverting .mp3 to audiobook format...")
    if CONVERT_TO_MP4:
        command = "ffmpeg -nostdin -loglevel fatal -stats -i ../output.part{:0>3}.aac -i {} -map_metadata 1 -y -vn -acodec copy ../output.part{:0>3}.mp4".format(part_number, audiobook_parts[part_number]['chapters_file_name'], part_number)
        subprocess.call(command.split(" "))

    # create tags, rename file
    audio = MP4("../output.part{:0>3}.mp4".format(part_number))
    if len(audiobook_parts) > 1:
        audio["\xa9nam"] = [album_title + ", Part {}".format(part_number)]
        audio["trkn"] = [(part_number, number_of_parts)]
        audio['cpil'] = True
    else:
        audio["\xa9nam"] = [album_title]
    audio["\xa9alb"] = [album_title]
    audio["\xa9ART"] = [album_artist]
    audio["desc"] = [album_description]
    audio["\xa9gen"] = ["Audiobook"]
    audio['\xa9cmt'] = "Downloaded from Internet Archive: " + item_url
    audio['\xa9too'] = "This audiobook was created by 'IA Audiobook Creator' https://github.com/vpoluyaktov/IA_audiobook_creator"
    audio['cprt'] = license_url
    audio['purl'] = item_url

    print("Adding audiobook cover image")
    # add album cover to the audiobook
    if ".PNG" in album_cover.upper():
        image_type = 14
    else:
        image_type = 13
    data = open(os.path.join(album_cover), 'rb').read()
    audio["covr"] = [MP4Cover(data, image_type)]

    audio.save()

    if len(audiobook_parts) > 1:
        audiobook_file_name = "{} - {}, Part {}.m4b".format(album_artist, album_title, part_number)
    else:
    	audiobook_file_name = "{} - {}.m4b".format(album_artist, album_title)

    # replace non-safe characters in the file name
    unsafe_tuples = [('/','_')]
    for tuple in unsafe_tuples:
        audiobook_file_name = audiobook_file_name.replace(tuple[0], tuple[1])

    os.rename("../output.part{:0>3}.mp4".format(part_number), "../{}".format(audiobook_file_name))

    # clean up
    if POST_CLEANUP:
        os.remove("../output.part{:0>3}.aac".format(part_number))
        os.remove("../audio_files.part{:0>3}".format(part_number))
        os.remove("../chapters.part{:0>3}".format(part_number))

    if len(audiobook_parts) > 1:
      print("\nPart {} created: output/{}\n".format(part_number, audiobook_file_name))
    else:
      print("\nAudiobook created: output/{}\n".format(audiobook_file_name))

    part_number += 1

# clean up
os.chdir("..")
if POST_CLEANUP:
    shutil.rmtree(item_id)
os.chdir("..")
