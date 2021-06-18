#!/bin/bash

FILE=`basename -- "$1"`

if [ -z "$FILE" ]; then
  echo "No file for upload is specified"
  exit 1
fi

mv "./output/$FILE" ./tmp/
dbxcli put "./tmp/$FILE" "/Audio/Internet Archive/$FILE"
