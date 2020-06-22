#!/usr/bin/env python
# encoding: utf-8

## downloads audio files from Internet Archive collection and create a .m4b audiobook
## Inspired by a code of Robin Camille Davis, Robert Orr and Benjamin Elbers


import os
import time
import sys
import internetarchive as ia
from requests.exceptions import HTTPError
from datetime import timedelta
import humanfriendly


search_condition = ""
items = {}
search_max_items = 10
item_number = None
item = None

while True:
    search_condition = input("Enter search condition or 'x' to exit: ")
    if (search_condition == 'x'):
        exit(0)
    if (len(search_condition) < 4):
        print("The search condition '{}' is too short".format(search_condition))
        continue

    # Don't forget to run 'ia configure' in your terminal before first start
    search = ia.search_items("title:('{}') AND mediatype:(audio)".format(search_condition))

    if (search.num_found == 0 or search.num_found > search_max_items):
        print("{} items found. It's too many. Try to clarify the search condition".format(search.num_found))
        continue

    print("{} items found:".format(search.num_found))
    print("===============================================================")

    num = 0
    for result in search: # for all items in a collection
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
try:
    ia.download(item_id, verbose=True, glob_pattern='*.mp3|*.jpg')
    print("Download success.\n\n")
except HTTPError as e:
    if e.response.status_code == 403:
     print("Access to this file is restricted.\nExiting")     
except Exception as e:
    print("Error Occurred downloading {}.\nExiting".format(e)) 
