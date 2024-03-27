#!/usr/bin/env bash

RED="\033[1;31m"
GREEN="\033[1;32m"
NC="\033[0m"
SELF_NAME=$(basename "$0")
VERBOSITY=1
RELATIVE_PATH_TO_UPDATE_DOCKER="sonic-tool/mars/scripts/update_docker.py"
BASEDIR=$(dirname $0)
PATH_TO_UPDATE_DOCKER="${BASEDIR}/../../../${RELATIVE_PATH_TO_UPDATE_DOCKER}"

################################
#                              #
# Script configuration section #
#                              #
################################
USAGE(){
    cat << EOF

${SELF_NAME}

Info:
     The script will print the NGTS version of a given sonic-mgmt repo
EOF
}

error(){
    if [[ ${VERBOSITY} -gt 0 ]]; then
        echo -e "${RED}[ERROR] $1${NC}"; exit 1
    fi
}

# Verify that file exists #
if [ ! -f "$PATH_TO_UPDATE_DOCKER" ]; then
    error "Upstream script RC=1 $PATH_TO_UPDATE_DOCKER does not exists."
fi

# Extract the SDK version from the README file #
NGTS_VERSION=$(cat $PATH_TO_UPDATE_DOCKER | grep \'docker-ngts\': | grep -oP '\d*\.\d*\.\d*')

# Verify that NGTS version isn't empty #
if [ -z "$NGTS_VERSION" ]; then
    error "Upstream script RC=1. Unable to extract the NGTS version from the update_docker.py file"
fi

echo "$NGTS_VERSION"
exit 0


