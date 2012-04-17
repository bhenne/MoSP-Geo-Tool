#!/bin/sh
export LD_LIBRARY_PATH=/usr/local/lib:/usr/local/lib64:`pwd`/lib:`pwd`/lib64
export PYTHONPATH=..:.
cd gui
python main_window.py
cd ..
