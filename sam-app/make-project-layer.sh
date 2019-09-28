#!/bin/bash
set -e

PROJECT_DIR=$1
ARCHIVE_PATH=$2
OLD_PWD=$PWD
TMP=$(mktemp -d)
PYPATH="$TMP/python/lib/python3.7/site-packages/"

mkdir -p "$PYPATH"

cp -a $PROJECT_DIR/. "$PYPATH"
cd $TMP
zip -r layer.zip python
cd "$OLD_PWD"
mv "$TMP/layer.zip" $ARCHIVE_PATH
rm -r "$TMP"
