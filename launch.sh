#!/bin/bash
for f in /scripts/*.sh
do
    if [ -f "$f" ]; then
        chmod +x "$f"
        "$f" &
    fi
done