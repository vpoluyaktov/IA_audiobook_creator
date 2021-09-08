# Internet Archive Audiobook Creator

## Description
There are thousands of free “old-time radio” shows, audiobooks, and lectures, available for download from the Internet Archive site (https://archive.org/). You can listen to them right in your web browser but if you would like to listen to the shows on your mobile device it is not very convenient - in most cases, they are provided as a set of single .mp3 files. You have to download all the files to your mobile device, create a playlist, always remember the last file and a position you have listened to.<br><br>
It would be much easier if there is a simple way to create an audiobook from a radio show or a book you like.<br><br>
That is why I developed this Python script. Using the script, all you need is a show or a book name or a direct link on archive.org. It will download the book .mp3 files, recode all of them with the same bit rate, produce a list of chapters (you can edit it in the middle of the process), and then it will create an audiobook in .m4b format.
<br><br>


## Hardware requirements and operation system
There are no specific hardware requirements for this script. I usually run it under tmux (or screen) on a 2 CPU 7.5 Gb Ubuntu host, launched in AWS or GCP.
Also, it was successfully tested on a MacBook laptop. I've never had a chance to test it on a Windows computer, but it should run if you install all software dependencies (see below).
<br><br>


## Dependencies

This script is written in Python, in particular on Python 3. So, first of all, you need to ensure you have python3 installed on your computer. If you don't, search Google for how to install Python3 on your operation system.<br>
Next, you need to install some python modules. The easiest way to do it is to use pip (preferred installer program). Usually, pip utility is installed with Python together, but if you don't have pip installed on your computer, then Google it. When just run the commands below:
```
pip install internetarchive
pip install humanfriendly
pip install mutagen
pip install audioread
pip install python-magic
```
The next thing you need to do is to install the FFmpeg utility. Depending on your operating system run:
```
# Linux (debian/ubuntu)
sudo apt-get install ffmpeg

# MacOS:
brew install ffmpeg
```
Or download and install it manually from https://ffmpeg.org/download.html <br>


And the last piece you need to install is an Internet Archive libs and command-line tool. Again, depending on your operating system run:
```
# Linux (debian/ubuntu)
sudo apt-get install internetarchive

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
The script installation is simple: just clone the github repository or download the script to some folder on your machine.
<br><br>

## Launching the script

<br><br>

## A disclaimer
Because the copyrights expired for most old-time radio shows and most of them are in Public Domain now, you can download and listen to them for free. But also there is some copyright content on the Internet Archive site. Please do respect others' legal rights and don't break a law. This script is just a tool, that helps you to create an audiobook. The author is not responsible for how you will use it in any way. This is your responsibility to obey the terms of an item copyright license.
