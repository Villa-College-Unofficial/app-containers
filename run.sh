#!/bin/bash

# Prevent run as non-root
if [ ! $(id -u) -eq 0 ]; then
   echo Please run as root.
   exit 1
fi

HERE="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

cd "$HERE"

if [ ! -d .venv ]; then
    python3 -m venv .venv
fi

source .venv/bin/activate
python3 -m pip install -r ./requirements.txt

if [ -z "$@" ]; then
    python3 src/main.py
else
    $@
fi
