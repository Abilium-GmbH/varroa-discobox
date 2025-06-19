#!/bin/bash

if [ ! -d "./venv" ]; then
    echo "Environment not setup, run the \"setup-python-env.sh\" script first."
    exit 1
fi


if [ -z $GENICAM_GENTL64_PATH ]; then
    current_path=$(pwd)

    source ./vimbax.config

    sdk_path=$path
    sdk_path=${sdk_path%"/"}

    cti_path=$(find $sdk_path -path "*/cti")
    cd $cti_path

    file=$(find . -name "Set*.sh")
    echo "file $file"
    source $file

    echo $GENICAM_GENTL64_PATH

    cd $current_path
fi

source ./venv/bin/activate
python discobox.py $@
