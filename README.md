# Queencubator: Queen of Biggest Incubator

There must be persona files in the personae directory and api keys in the scripts/secrets directory stored in env files for each bot being deployed. New bots and decommisioned bots need to be listed in the bots/{newbots},{decomission} files.
The setup script will run on a pull request or if  you run the make commands: build, test, up and push.
The script make commands have down as a dependancy so that it shuts down the running instances before making changes. In order to decomission running containers the bots need to remain in the existing docker-compose files until after the make down command is run. Then the script generates new compose files.
The bots file will maintain a list of all bots that get added and decomissioned. It instead checks the decommission file to know what bots get ignored. As long as a bot is listed here it will not get generated even though it exists in the bots file.
Bots from the newbots file will get amended to the bots file. They can be deleted from this file after deployed and they will remain active in the bots file. They can remain in the newbots file and not get duplicated.
Two docker-compose files get generated using the bots from the bots file ignoring the bots listed in the decomission file.
The docker-compose files must remain in the root directory until the next time make down is run. The docker-compose down command won't know what bots to remove if the docker-compose files are modified before the decomissioned bots are shut down. The setup script will then generate new docker-compose files reflecting the decomissioned bots.

Instructions:
1.List the new bots being added &/or the bots being decomissioned to the appropriate files.
2. Add secrets to the appropriate location.
3. Deploy using the make build, test, up commands.
