#!/bin/bash

# Identifies the scripts in the scripts directory
FILE=$(ls scripts/secrets/*.env)
# Loop that removes the path to the script and the .sh producing a list of filenames
for X in $FILE; do
  Y=${X%.env};
  BOT=${Y##*/}
    for FILENAME in $BOT; do
        export PERSONAE=$FILENAME;
        cat templates/botscript.template | envsubst > scripts/"$FILENAME".sh;
	chmod +x scripts/*.sh
    done
done
	
