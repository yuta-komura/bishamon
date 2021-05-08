#!/bin/sh

SCRIPT_DIR=$(
    cd $(dirname $0)
    cd ../
    pwd
)

. ${SCRIPT_DIR}/venv/bin/activate

python ${SCRIPT_DIR}/insert_ohlcv_1min_bitflyer.py &

wait