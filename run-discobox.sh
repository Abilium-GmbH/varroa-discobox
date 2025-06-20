#!/bin/bash

if [ ! -d "./venv" ] || [ ! -f "./vimbax.config" ]; then
    echo "Environment not setup, run the \"setup-python-env.sh\" script first."
    exit 1
fi

source ./vimbax.config

if [ ! -n "$path" ]; then
    echo "The vimbax.config file does not contain a path variable."
    echo "Run the \"setup-python-env.sh\" script again to fix this issue."
    exit 1
elif [ ! -d "$path" ]; then
    echo "The specified path \"$path\" in vimbax.config is invalid."
    exit 1
fi


sdk_path=$path
sdk_path=${sdk_path%"/"}

cti_path=$(find $sdk_path -path "*/cti")

export GENICAM_GENTL64_PATH=:$cti_path

source ./venv/bin/activate

python3 discobox.py $@
