#!/bin/bash

if [ ! -d "./venv" ]; then
    echo "Environment not setup, run the \"setup-python-env.sh\" script first."
    exit 1
fi

source ./venv/bin/activate

python discobox.py $@
