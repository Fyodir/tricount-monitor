#!/bin/bash

set -e

source /home/andysmith/.tricount.env

DATETIME_NOW=$(date +%y%m%d)

printf "%s\n" "$DATETIME_NOW"

cd /home/andysmith/tricount-extractor-pi

/home/andysmith/tricount-extractor-pi/.venv/bin/python \
    /home/andysmith/tricount-extractor-pi/extract_balances.py \
   ${TRICOUNT_KEY} 

git add docs/
git diff --cached --quiet || git commit -m "Update generated docs - ${DATETIME_NOW}"
git push origin master
