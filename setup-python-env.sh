#!/bin/bash

print_usage() {
    echo "Usage:"
    echo "    $0 <VimbaX SDK Path>"
    echo ""
    echo "e.g., $0 ../VimbaX_Setup-2025-1-Linux64"
}

if [ $# -ne 1 ]; then
    print_usage
    exit 1
elif [ ! -d $1 ]; then
    echo "\"$1\" is not a valid path"
    echo ""
    print_usage
    exit 1
fi

sdk_path=$1
sdk_path=${sdk_path%"/"}

printf "path=$sdk_path" > vimbax.config

file=$(find $1 -path "*/api/python/*" -name "*.whl")

sudo apt update
sudo apt -y install python3-tk

python3 -m venv venv
source ./venv/bin/activate
pip install -r requirements.txt
pip install $file[numpy,opencv]
