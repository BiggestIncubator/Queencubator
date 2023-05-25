#!/bin/bash
<<<<<<< HEAD
for f in scripts/*.sh
=======

script_dir=$(dirname "$0")

for f in "$script_dir"/scripts/*.sh
>>>>>>> origin
do
    if [ -f "$f" ]; then
        chmod +x "$f"
        konsole -e "$f" &
    fi
done
