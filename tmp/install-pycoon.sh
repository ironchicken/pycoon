#!/bin/bash

if [ $# != 1 ]
then
    echo Please specify Python version [2.3, 2.4]
    exit 1
fi

PY_VERSION=$1

PYCOON_ROOT=..
PYCOON_SRC=$PYCOON_ROOT/src/pycoon
PYCOON_LIB=/usr/local/lib/python${PY_VERSION}/site-packages/pycoon
SERVER_CONF_SRC=$PYCOON_ROOT/conf/server.xml
SERVER_CONF_LIB=/etc/pycoon/server.xml
SERVER_RESOURCES_SRC=$PYCOON_ROOT/conf/resources
SERVER_RESOURCES_LIB=/etc/pycoon/resources

cp -v $PYCOON_SRC/*.py $PYCOON_LIB

DIRS="
authenticators
generators
matchers
selectors
serializers
transformers
"

for dir in $DIRS
do
  d_lib=$PYCOON_LIB/$dir
  if [ ! -d $d_lib ]
  then
      mkdir -vp $d_lib
  fi
  cp -v $PYCOON_SRC/$dir/*.py $d_lib
done

cp -v $SERVER_CONF_SRC $SERVER_CONF_LIB
cp -v $SERVER_RESOURCES_SRC/* $SERVER_RESOURCES_LIB