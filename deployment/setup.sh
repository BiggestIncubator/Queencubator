#!/bin/bash

set -eu

cd "$(dirname "$0")."

# Prints the header for the docker compose file and override file
printf "version: '3.7'\nservices:\n" > docker-compose.yaml
printf 'services:\n' > docker-compose.override.yaml

# Identifies the scripts in the scripts directory
# FILE=$(ls scripts/secrets/*.env)
FILE=$(cat newbot.txt)

# Loop that generates entries in the compose file and override file for each bot
# Generates launch script for each bot if a key file exists in scripts/secrets
for FILENAME in $FILE; do
   export PERSONAE=$FILENAME;
   cat templates/docker-compose.template | envsubst >>  docker-compose.yaml;
   cat templates/docker-compose.override.template | envsubst >> docker-compose.override.yaml;
   cat templates/botscript.template | envsubst > scripts/"$FILENAME".sh;
   chmod +x scripts/*.sh
done

