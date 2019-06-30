#!/bin/sh

set -e

DOCS_FOLDER="./doc"
RM_FILENAME="$DOCS_FOLDER/SiM3U1xx-SiM3C1xx-RM.pdf"
RM_LINK=https://www.silabs.com/documents/public/data-sheets/SiM3U1xx-SiM3C1xx-RM.pdf
SVD_TMP_OUT="$(mktemp)"
SVD_OUT=./sim3u.svd

mkdir -p $DOCS_FOLDER

if [ ! -f $RM_FILENAME ]; then
    wget $RM_LINK -O $RM_FILENAME
fi

pipenv install
pipenv run python src/parse_sim3u.py --input $RM_FILENAME --out $SVD_TMP_OUT
xmllint --format $SVD_TMP_OUT > $SVD_OUT
rm $SVD_TMP_OUT
