#!/bin/sh

SCRIPT_DIR=$(
    cd $(dirname $0)
    pwd
)

sh ${SCRIPT_DIR}/main/trading.sh &

wait
