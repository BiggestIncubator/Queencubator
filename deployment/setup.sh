#!/bin/bash

set -eu
cd "$(dirname "$0")."

# Decomission bots
# Checks decomission file for bots to remove, lists bots to remove as DECOM ignoring active bots
if [ -s bots/decomission ]; then
	DECOM=$(comm -12 <(sort bots/decomission) <(sort bots/bots))
fi
# New bots
# Checks newbots for bots to add, lists bots to keep as a string. Ignores existing bots.
if [ -s bots/newbots ]; then
	NEWBOTS=$(comm -23 <(sort bots/newbots) <(sort bots/bots))
fi
# Defines bots for docker-compose file and writes new bots to the bots file
REMAINING=$(comm -3 <(sort bots/decomission) <(sort bots/bots))
ACTIVEBOTS="$REMAINING $NEWBOTS"
for BOTSFILE in $NEWBOTS; do 
	echo $BOTSFILE >> bots/bots
done

# Prints the header for the docker compose file and override file
printf "version: '3.7'\nservices:\n" > docker-compose.yaml
printf 'services:\n' > docker-compose.override.yaml

for FILENAME in $ACTIVEBOTS; do
   export PERSONAE=$FILENAME;
   cat templates/docker-compose.template | envsubst >>  docker-compose.yaml;
   cat templates/docker-compose.override.template | envsubst >> docker-compose.override.yaml;
   cat templates/botscript.template | envsubst > scripts/"$FILENAME".sh;
   chmod +x scripts/*.sh
done

