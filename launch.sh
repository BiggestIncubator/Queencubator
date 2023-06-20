#!/bin/bash

script_dir=$(dirname "$0")
pids=()

# Function to kill spawned processes
cleanup() {
    for pid in "${pids[@]}"; do
        kill "$pid" 2> /dev/null
    done
}

# Trap termination signals and call cleanup function
trap cleanup SIGINT SIGTERM SIGHUP

for f in "$script_dir"/scripts/*.sh
do
    if [ -f "$f" ]; then
        chmod +x "$f"
        "$f" &
        pids+=("$!")
    fi
done

# Wait for all spawned processes to finish
wait