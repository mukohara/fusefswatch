#!/bin/bash

if [ $1 == "-u" ]; then
    cd /
    umount /fuse-watch
    sudo unlink /home/mukohara
    sudo mv /home/mukohara.fuse-watch /home/mukohara
elif [ $1 == "-c" ]; then
    python /home/mukohara/git/fusefswatch/converter.py /var/log/fuse-atch.log
else
    /home/mukohara/git/libfuse/example/passthrough /fuse-watch
    sudo mv /home/mukohara /home/mukohara.fuse-watch
    if [ ${1: -1}  == "/" ]; then
        path=${1/%?/}
        sudo ln -s /fuse-watch/home/mukohara.fuse-watch $path
    else
        sudo ln -s /fuse-watch/home/mukohara.fuse-watch $1
    fi
fi
