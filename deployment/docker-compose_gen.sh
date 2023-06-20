#!/bin/bash

set -eu

cd "$(dirname "$0")."

# Prints the header for the docker compose file and override file
printf "version: '3.7'\nservices:\n" > docker-compose.yaml
printf 'services:\n' > docker-compose.override.yaml

# Identifies the scripts in the scripts directory
FILE=$(ls scripts/*.sh)

# Loop that removes the path to the script and the .sh producing a list of filenames
for LIST in $FILE; do
  X=$LIST;
  Y=${X%.sh};
  BOT=${Y##*/};
# Loop that generates entries in the compose file and override file for each bot
    for FILENAME in $BOT; do
      export PERSONAE=$FILENAME;
      cat templates/docker-compose.template | envsubst >>  docker-compose.yaml;
      cat templates/docker-compose.override.template | envsubst >> docker-compose.override.yaml
    done
done
