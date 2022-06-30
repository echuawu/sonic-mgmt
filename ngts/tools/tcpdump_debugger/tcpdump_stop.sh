#!/bin/sh
if [ -f /var/run/$1.pid ]
then
        kill `cat /var/run/$1.pid`
        echo tcpdump `cat /var/run/$1.pid` killed.
        rm -f /var/run/$1.pid
else
        echo tcpdump not running.
fi
