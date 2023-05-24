#!/bin/bash

script_dir=$(dirname "$0")

for f in "$script_dir"/scripts/*.sh
do
    if [ -f "$f" ]; then
        chmod +x "$f"
        konsole -e "$f" &
    fi
done