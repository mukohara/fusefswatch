#!/bin/bash

if [ $1 == "-u" ]; then
    cd /
    umount /fuse-watch
    sudo unlink /home/mukohara
    sudo mv /home/mukohara.fuse-watch /home/mukohara
elif [ $1 == "-c" ]; then
    python /home/mukohara/git/fusefswatch/converter.py /var/log/fuse-watch.log
else
    /home/mukohara/git/libfuse/example/passthrough /fuse-watch
    sudo mv /home/mukohara /home/mukohara.fuse-watch
    sudo ln -s /fuse-watch/home/mukohara.fuse-watch${1:14} $1
fi

