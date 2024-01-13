# Internet Archive Audiobook Creator

## This repository has been archived and is no longer supported in favor of newest version of the Audiobook Builder https://github.com/vpoluyaktov/abb_ia

## Description
There are thousands of free “old-time radio” shows, audiobooks, and lectures, available for download from the Internet Archive site (for example  https://archive.org/details/oldtimeradio). You can listen to them right on your web browser but if you would like to listen to the shows on your mobile device it is not very convenient - in most cases, they are provided as a set of single .mp3 files. You have to download all the files to your mobile device, create a playlist, always remember the last file and position you have listened to.<br>

It would be much easier if there was a simple way to create an audiobook from a radio show or a book you like.<br>

That is why I developed this Python script. Using the script, all you need is a show or a book name or a direct link on archive.org. It will download the book .mp3 files, re-encode all of them with the same bit rate, produce a list of chapters (you can edit it in the middle of the process), and then it will create an audiobook in .m4b format.<br>

This work was inspired by a code of Robin Camille Davis, Robert Orr and Benjamin Elbers. Thank you guys!
<br><br>


## Hardware requirements and operation system
There are no specific hardware requirements for this script. I usually run it on my Macbook or on a 2 CPU 7.5 Gb AWS Ubuntu host. I haven't had a chance to test it on a Windows computer, but it should run if you install all software dependencies (see below). 
<br><br>


## Dependencies

This script is written in Python, in particular in Python 3. So, you need to ensure you have python 3 installed on your computer. If you don't, search Google for how to install Python3 on your operating system.<br>

Next, you need to install some python modules. The easiest way to do it is to use pip (preferred installer program). Usually, the pip utility is installed with Python together, but if you don't have pip installed on your computer, then Google it. Then just run the commands below:
```
pip install internetarchive
pip install humanfriendly
pip install mutagen
pip install audioread
pip install python-magic
pip install html2text
```
The next thing you need to do is to install the FFmpeg utility. Depending on your operating system run:
```
# Linux (debian/ubuntu)
sudo apt-get install ffmpeg
sudo apt-get install libmagic

# Linix (alpine)
sudo apk add ffmpeg
sudo apk add libmagic

# MacOS:
brew install ffmpeg
brew install libmagic
```
Or download and install it manually from https://ffmpeg.org/download.html <br>


And the last piece you need to install is an Internet Archive libs and command-line tool. Again, depending on your operating system run:
```
# Linux (debian/ubuntu)
sudo apt-get install internetarchive

# Linix (alpine)
sudo apk add internetarchive

# MacOS:
brew install internetarchive
```
If you are planning to perform a search using this script on the archive.org site, you need to create your personal archive.org account (it is not required if you always provide a direct link on a book or show on archive.org). Just go to https://archive.org/account/signup and register a new account for yourself. <br>
Then run:
```
ia configure
```
and enter your archive.org username and password
<br><br>

## Installation
The script installation is simple: just clone the github repository (`git clone https://github.com/vpoluyaktov/IA_audiobook_creator.git`) or download the script to some folder on your machine. Don't forget to make the file executable (`chmod u+x ./IA_audiobook_creator`) if you download the script manually.
<br><br>

## Launching the script
To lauchch the script and create an audiobook, first find a radio show or a book on archive.org you want to listen too.
For example I want to create an audiobook from this show: https://archive.org/details/OTRR_Murder_By_Experts_Singles<br>
<img src="https://user-images.githubusercontent.com/1992836/132761388-f267b94e-f93b-4134-93e3-3296e548fa3a.png" width="800">


<br>
Open a terminal, go to the directory where you downloaded the script and launch it by the followig command:

```
 ./IA_audiobook_creator.py
``` 

Next, you need to provide a radio show or book name to the script. Also you can use a direct link to the item on archive.org.
For my particular case it can be either `Murder By Experts - Single Episodes` or https://archive.org/details/OTRR_Murder_By_Experts_Singles <br>
The script will ask you to confirm the item you want to download. You need to select an item number from the list.

```
./IA_audiobook_creator.py

Internet Archive audiobook creator script

Enter search condition or 'x' to exit: Murder By Experts
8 items found:
===============================================================
1:      Murder By Experts (10 file(s), duration: 04:54:09, size: 70.6 MB)
2:      Murder By Experts (1 file(s), duration: 00:26:49, size: 6.44 MB)
3:      Murder By Experts (Page 2) (5 file(s), duration: 02:30:06, size: 65.41 MB)
4:      Murder By Experts (0 file(s), duration: 00:00:00, size: 0.0 bytes)
5:      Murder By Experts - Single Episodes (15 file(s), duration: 07:24:13, size: 426.48 MB)
6:      Podcast #78 Murder By Experts (1 file(s), duration: 02:00:20, size: 57.78 MB)
7:      MURDER BY EXPERTS / ALAN YOUNG (1 file(s), duration: 02:32:41, size: 74 MB)
8:      Murder By Experts "Dig Your Own Grave" (1 file(s), duration: 00:29:51, size: 7.17 MB)

Enter item number for download, 's' for new search or 'x' to exit: 5
```
Next prompt will allow you to change the audiobook name and author if you would like. Also you may want to edit the audio book chapters if you don't like names grabbed from the Internet Archive site:

```
Audiobook Name [Murder By Experts]:
Audiobook Author [OTRR]:

 Would you like to edit chapter names at the end of the book creation? [y/N]

```
If estimated audiobook size is bigger than an threshold (2 Gb by default), the audiobook will be splitted by parts (so the script will create multipart .m4b audiobook). You can change a part size if you would like:
```
The audiobook total size (31.13 GB) is bigger than default single part size (2 GB), so the book will be split into 16
parts.

 Would you like to change default part size? [y/N] y

Enter new part size (Mb, Gb): 3 Gb

```

If the radio show or a book you want to download doesn't have a cover image on Internet Archive site, the script will ask you if you want to use default AI image, a local file or download some image from the Internet:
```
Downloading album covers
No cover image found for this item.
You have three options:
 1) Use default Internet Archive logo
 2) Use an image from Internet
 3) Use local picture file
 Your choice: 2
Enter a picture url (.jpeg or .png format): https://i.pinimg.com/post-free-ads-antique-radio.jpg

```

The script will start a download process. It may take a while, depending on the audiobook size and your connection bandwidth, so be patient. I usually run the script under tmux (or screen) on a cloud Ubuntu host launched in AWS or GCP. It allows me to close my Macbook any time without the script interruption and re-connect to the cloud host when the process is complete.
```
Downloading item #5:    Murder By Experts - Single Episodes (15 files)

Downloading album covers
    OTRR_Certified_Murder_By_Experts.jpg...                                                    OK
    OTRR_Certified_Murder_By_Experts_thumb.jpg...                                              OK

Downloading mp3 files
     1/15: Murder_by_Experts_49-06-13_001_Summer_Heat.mp3 (27.43 MB)...                        OK
     2/15: Murder_by_Experts_49-07-04_004_Two_Coffins_To_Fill.mp3 (28.49 MB)...                OK
     3/15: Murder_by_Experts_49-07-11_005_Prescription_for_Murder.mp3 (28.54 MB)...            OK
     4/15: Murder_by_Experts_49-07-18_006_The_Creeper.mp3 (28.65 MB)...                        OK
     5/15: Murder_by_Experts_49-07-25_007_The_Big_Money.mp3 (27.88 MB)...                      OK
     6/15: Murder_by_Experts_49-08-08_009_The_Dark_Island.mp3 (28.56 MB)...                    OK
     7/15: Murder_by_Experts_49-08-15_010_Dig_Your_Own_Grave.mp3 (28.24 MB)...                 OK
     8/15: Murder_by_Experts_49-08-29_012_Its_Luck_That_Counts.mp3 (28.27 MB)...               OK
     9/15: Murder_by_Experts_49-09-05_013_Return_Trip.mp3 (28.6 MB)...                         OK
    10/15: Murder_by_Experts_49-09-12_014_I_Dreamt_I_Died.mp3 (28.52 MB)...                    OK
    11/15: Murder_by_Experts_49-09-26_016_The_Unseeing_Witness.mp3 (28.73 MB)...               OK
    12/15: Murder_by_Experts_49-12-26_029_The_Case_of_the_Missing_Mind.mp3 (28.72 MB)...       OK
    13/15: Murder_by_Experts_50-04-17_045_Two_Can_Die_as_Cheaply_as_One.mp3 (28.55 MB)...      OK
    14/15: Murder_by_Experts_50-04-24_046_Conspiracy.mp3 (28.92 MB)...                         OK
    15/15: Murder_by_Experts_50-05-22_050_Threes_a_Crowd.mp3 (28.39 MB)...                     OK
```
Next stage is re-encoding downloaded .mp3 files with the same bit rate to avoid incorrect joining to a single audio file:
```
Re-encoding .mp3 files all to the same bitrate and sample rate...
     1/15: Murder_by_Experts_49-06-13_001_Summer_Heat.mp3...                   OK
     2/15: Murder_by_Experts_49-07-04_004_Two_Coffins_To_Fill.mp3...           OK
     3/15: Murder_by_Experts_49-07-11_005_Prescription_for_Murder.mp3...       OK
     4/15: Murder_by_Experts_49-07-18_006_The_Creeper.mp3...                   OK
     5/15: Murder_by_Experts_49-07-25_007_The_Big_Money.mp3...                 OK
     6/15: Murder_by_Experts_49-08-08_009_The_Dark_Island.mp3...               OK
     7/15: Murder_by_Experts_49-08-15_010_Dig_Your_Own_Grave.mp3...            OK
     8/15: Murder_by_Experts_49-08-29_012_Its_Luck_That_Counts.mp3...          OK
     9/15: Murder_by_Experts_49-09-05_013_Return_Trip.mp3...                   OK
    10/15: Murder_by_Experts_49-09-12_014_I_Dreamt_I_Died.mp3...               OK
    11/15: Murder_by_Experts_49-09-26_016_The_Unseeing_Witness.mp3...          OK
    12/15: Murder_by_Experts_49-12-26_029_The_Case_of_the_Missing_Mind.mp3...  OK
    13/15: Murder_by_Experts_50-04-17_045_Two_Can_Die_as_Cheaply_as_One.mp3... OK
    14/15: Murder_by_Experts_50-04-24_046_Conspiracy.mp3...                    OK
    15/15: Murder_by_Experts_50-05-22_050_Threes_a_Crowd.mp3...                OK

```
Then the script will do some magic trying to build nice and clear chapter names. You can edit the chapter titles if you would like in separate terminal window:
```
Creating audiobook chapters
Chapter   1 (00:28:33): Summer Heat
Chapter   2 (00:29:40): Two Coffins To Fill
Chapter   3 (00:29:43): Prescription for Murder
Chapter   4 (00:29:50): The Creeper
Chapter   5 (00:29:02): The Big Money
Chapter   6 (00:29:44): The Dark Island
Chapter   7 (00:29:24): Dig Your Own Grave
Chapter   8 (00:29:26): It's Luck That Counts
Chapter   9 (00:29:47): Return Trip
Chapter  10 (00:29:42): I Dreamt I Died
Chapter  11 (00:29:55): The Unseeing Witness
Chapter  12 (00:29:54): The Case of the Missing Mind
Chapter  13 (00:29:44): Two Can Die as Cheaply as One
Chapter  14 (00:30:07): Conspiracy
Chapter  15 (00:29:34): Three's a Crowd

```
Final stage is to combine the single .mp3 files in to a single one and create the audiobook .m4b file:
```
Combining single .mp3 files into big one...
Estimated duration of the book: 07:24:12.141
size=  387952kB time=07:25:33.57 bitrate= 118.9kbits/s speed=17.7x

Converting .mp3 to audiobook format...
size=  384587kB time=07:25:32.11 bitrate= 117.9kbits/s speed=2.59e+03x
Adding audiobook cover image

Audiobook created: output/OTRR - Murder By Experts.m4b
```
You can use included upload.sh script to upload the audiobook to your Dropbox account (you need to install `dbxcli` utility for this).

This is how the audiobook looks like in MacOS iBooks app 

<img src="https://user-images.githubusercontent.com/1992836/132757995-7d1583c1-6562-4d32-ab8b-4ee2238ba30f.png" width="800">
<br><br><br>

and on my IPhone (I use [BookPlayer](https://apps.apple.com/us/app/bookplayer/id1138219998) app)<br>
<img src="https://user-images.githubusercontent.com/1992836/132761248-d29d3e2c-cf99-4b48-9f74-6361f9334d26.png" width="600">


<br><br>

## Disclaimer
Because the copyrights expired for most old-time radio shows and most of them are in Public Domain now, you can download and listen to them for free. But also there is some copyright content on the Internet Archive site. Please do respect others' legal rights and don't break the law. This script is just a tool that helps you create an audiobook. The author is not responsible for how you use it in any way. This is your responsibility to obey the terms of an item copyright license.
