#!/bin/bash

DROP_BOX_BASE_DIR="/Audio/Internet Archive"
DESTINATION=$1

if [ -z "$DESTINATION" ]; then
  echo "No Dropbox destination is specified. Exiting"
  exit 1
fi

FILES=$(find ./output -name "${DESTINATION}*.m4b" 2>/dev/null)
if [ -z "$FILES" ]; then
    echo "No files found. Exiting"
    exit 1
fi 

NUMBER_OF_FILES=$(echo "$FILES" | wc -l)

DROPBOX_UPLOAD_DIR=""

if [ $NUMBER_OF_FILES -gt 1 ]; then
  DROPBOX_UPLOAD_DIR=$DESTINATION
fi
echo $NUMBER_OF_FILES
echo "File(s) will be uploaded to ${DROP_BOX_BASE_DIR}/${DROPBOX_UPLOAD_DIR}/"


echo "Moving files to ./tmp dir..."
if [ ! -d ./tmp ]; then
  mkdir ./tmp
fi

IFS='
'
for file in $FILES; do 
  FILE=`basename -- "$file"`
  echo "$FILE"
  mv "./output/${FILE}" "./tmp/${FILE}"
done

echo -e "\nUploading files to Dropbox..."
for file in $FILES; do
  FILE=`basename -- "$file"`
  echo "$FILE"
  dbxcli put "./tmp/$FILE" "${DROP_BOX_BASE_DIR}/${DROPBOX_UPLOAD_DIR}/$FILE"
done

exit 0
