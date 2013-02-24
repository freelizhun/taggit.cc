#!/bin/bash
# usage
# ./start_service.sh debug
# ./start_service.sh prod
protoc --python_out=.  --proto_path=../proto ../proto/taggit.proto
MODE=$1
if [ -z "$1" ]; then
    echo "default mode set to: debug"
    MODE="debug"
fi
python2 ps_launcher.py --mode $MODE
