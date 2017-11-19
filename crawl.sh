#!/bin/bash

if ! [[ $3 =~ [0-9]+ ]]; then
    echo "Please give a pure digit book id, $3 is not an acceptable book id."
    exit -1
fi

scrapy crawl SafariBooks -a user=$1 -a password=$2 -a bookid=$3
kindlegen *.epub
