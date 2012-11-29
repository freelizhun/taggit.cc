#!/bin/bash
# usage
# ./start_service.sh debug
# ./start_service.sh prod
protoc --python_out=.  --proto_path=../proto ../proto/taggit.proto
python2 ps_launcher.py --port 8080 --mode $1
