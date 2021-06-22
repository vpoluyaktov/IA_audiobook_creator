#!/bin/bash

DROPBOX_BASE_DIR="/Audio/Internet Archive"
DESTINATION="$1"

if [ -z "$DESTINATION" ]; then
  echo "No Dropbox destination is specified. Exiting"
  exit 1
fi

FILES=$(find ./output -name "${DESTINATION}*.m4b" 2>/dev/null | sort)
if [ -z "$FILES" ]; then
    echo "No files found. Exiting"
    exit 1
fi 

NUMBER_OF_FILES=$(echo "$FILES" | wc -l)


if [ $NUMBER_OF_FILES -eq 1 ]; then
  DROPBOX_UPLOAD_PATH="${DROPBOX_BASE_DIR}"
else
  DROPBOX_UPLOAD_PATH="${DROPBOX_BASE_DIR}/${DESTINATION}"
fi
echo "File(s) will be uploaded to ${DROPBOX_UPLOAD_PATH}/"

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
  dbxcli put "./tmp/$FILE" "${DROPBOX_UPLOAD_PATH}/$FILE"
done

exit 0
