#/bin/bash

#######################################################################################################
#                                                                                                     #
# To use: ./generated_deploy.sh -t {{ vault token }} -p {{ secret path }} -f {{ project }}            #          
#                               -v {{ secret var name }} -v {{ secret var name }}                     #
# Ex: ./generated_deploy.sh -t s.xxx -p dev/data/Livejam-Deployment -f /tmp                           #
#                           -v TICKET_SERVICE_ENV_DEV1 -v TICKET_SERVICE_ENV_DEV2			          #
#                                                                                                     #
#######################################################################################################

tag=$(git describe --always --tags --dirty --abbrev=7)
declare -a local_env deploy_env env_array vault_secret_array

get_env_array_name () {
	# Get array as input, sort it, cut all line that not contains '=' 
	# Get name before '=' in each line
	# Return array as global env_array

	local full_list
	env_array=()
	readarray -t full_list < <(for a in "${@}"; do echo "$a"; done | sort)
	for env in "${full_list[@]}"
	do
		if ( [[ ! -z ${env} ]] && [[ ${env} == *[=]* ]] ); then
		env_array+=($(echo ${env} | awk -F "=" '{print $1}'))
		fi
	done
}

# Check input
while getopts ":t:p:f:v:" opt; do
	case $opt in
		t) if [[ ${OPTARG} =~ ^(s|hvs).[A-Za-z0-9]*$ ]]; then
				VAULT_TOKEN=${OPTARG}
			else
				echo "Invalid Vault token. The vault should be s.xxx/hvs.xxx format"
				exit 1;
			fi
			;;
		p) if [[ ${OPTARG} = */data* ]]; then
				SECRET_PATH=${OPTARG}
			else
				echo "Invalid secret path. The secret path should be in {{ KV engine }}/data/{{ secret path }}"
				exit 1;
			fi
			;;
		f) if ( [[ ${#OPTARG} -ge 1 ]] ); then
				PROJECT_FOLDER=${OPTARG}
			else
				echo "Invalid path to export the project name."
				exit 1;
			fi
			;;
		v) if ( [[ ${OPTARG} =~ ^[A-Za-z0-9_-]* ]] && [[ ${#OPTARG} -ge 1 ]] ); then
				SECRET_VAR+=("${OPTARG}")
			else
				echo "Invald secret name. The secret name should start with A-Z, a-z, 0-9, _, and -"
			fi
			;;
	esac
done
shift $((OPTIND -1))

# Prepare deployment folder
tmpdir=$(mktemp -d -t dev-XXXXXXXXXX)
mkdir -p ${tmpdir}/deployment/${PROJECT_FOLDER}
envfile=${tmpdir}/deployment/${PROJECT_FOLDER}/.env
echo -n "" > $envfile

# Add docker-compose file and .env
if test -f "docker-compose.yaml"; then
	cat docker-compose.yaml > ${tmpdir}/deployment/${PROJECT_FOLDER}/docker-compose.yaml
fi

if test -f "docker-compose.server.yaml"; then
	cat docker-compose.server.yaml | grep -v shared_buffers > ${tmpdir}/deployment/${PROJECT_FOLDER}/docker-compose.server.yaml
fi

# Get secret from Vault to array
for secret in "${SECRET_VAR[@]}"; do
	raw_vault_secret=`curl -s  --header "X-Vault-Token: ${VAULT_TOKEN}" https://vault.biggestfan.net/v1/${SECRET_PATH} | jq --raw-output .data.data.${secret}`
	IFS=$'\n' read -rd '' -a v_array <<< "$raw_vault_secret"
	vault_secret_array+=( "${v_array[@]}" )
done
get_env_array_name ${vault_secret_array[@]//#*/}
deploy_env=("${env_array[@]}")

# Compare the env vars with .env if available
if [ -f .env ]; then
	# Get the array for local env
	readarray -t local_list < <(cat .env)
	get_env_array_name ${local_list[@]//#*/}
	local_env=("${env_array[@]}")

	# Compare deploy and local env vars
	if [ "${deploy_env[*]}" != "${local_env[*]}" ]; then
		echo "The environment variables on .env does not match with environment variable(s). Please check your environment varaiable(s)."
		echo "To debug:"
		echo "Deploy var:"
		echo "${deploy_env[@]}"
		echo "Local var:"
		echo "${local_env[@]}" 
	exit 1
	fi
fi 

# Add env var to env file for deployment
SERVICE=${PWD##*/}
tag_name=${SERVICE//-/_}
tag_name=$(echo ${tag_name} | tr a-z A-Z)
eval echo "TAG_\${tag_name}=\${tag}" > ${envfile}

for env in "${vault_secret_array[@]}"
do
	if ( [[ ! -z ${env} ]] && [[ ${env} == *[=]* ]] ); then
		echo "${env}" >> ${envfile}
	fi
done

#Add deploy scipt to deploy on target server
cp deployment/deploy.sh ${tmpdir}/deployment/${PROJECT_FOLDER}

# Compress file to local repo for CI
tar -cvf deployment.tgz -C $tmpdir ./
