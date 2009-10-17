#!/bin/bash
sudo ln -s `pwd`/src-clutter-1.0 /usr/lib/python2.5/site-packages/gstviewperf
sudo ln -s `pwd`/src-clutter-1.0/gst-viewperf /usr/bin/gst-viewperf
sudo chmod +x /usr/bin/gst-viewperf
