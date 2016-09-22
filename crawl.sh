#!/bin/sh
scrapy crawl SafariBooks -a user=$1 -a password=$2 -a bookid=$3
kindlegen *.epub