#!/bin/bash
echo
echo "*********************************************************************************"
echo "Welcome to the manual merge."
echo "This script simulates the job sonic_mgmt_merge until the 'solve conflicts' part."
echo "It will create a new folder for you to solve the conflicts on."
echo "format: ./manual_merge.sh <local branch> <github branch>"
echo "*********************************************************************************"
echo

if [ $# -lt 2 ]
  then
    echo "ERROR - Please give the name of the local branch and the github branch you want to run on."
    echo "        Format: ./manual_merge.sh <local branch> <github branch>"
    echo "        Example: ./manual_merge.sh develop master"
    exit 1
fi


tmp_dir="sonic-mgmt_$(date '+%Y_%m_%d-%H_%M_%S')"
GITHUB_REPOSITORY=https://github.com/Azure/sonic-mgmt.git
LOCAL_BRANCH=$1
GITHUB_BRANCH=$2
echo "LOCAL_BRANCH=${LOCAL_BRANCH}"
echo "GITHUB_BRANCH=${GITHUB_BRANCH}"

echo "Cloning sonic-mgmt (branch ${LOCAL_BRANCH}) into $(tmp_dir)"
git clone -b ${LOCAL_BRANCH} "ssh://l-sw-gerrit-01.mtl.labs.mlnx:29418/switchx/sonic/sonic-mgmt" -b ${LOCAL_BRANCH} ${tmp_dir}
cd ${tmp_dir} || exit 1
FILE=".git/hooks/commit-msg"
if [[ ! -f "$FILE" ]]; then
    echo "$FILE does not exists. copying commit message"
    scp -p -P 29418 l-sw-gerrit-01.mtl.labs.mlnx:hooks/commit-msg ".git/hooks/"
fi
echo "merging upstream/${GITHUB_BRANCH}"
git remote add upstream ${GITHUB_REPOSITORY} && git fetch upstream
git merge upstream/${GITHUB_BRANCH} --no-ff

echo
echo "*********************************************************************************"
echo "script passed well. your folder is ready here: ${tmp_dir}"
echo "1. cd ${tmp_dir}"
echo "2. Fix the conflicts."
echo "3. Commit to gerrit:"
echo "   git commit -m 'Merge remote-tracking branch 'upstream/${GITHUB_BRANCH}' into ${LOCAL_BRANCH}'"
echo "4. git review"
echo "5. Trigger the jenkins job http://fit81.mtl.labs.mlnx:8080/job/sonic_mgmt_merge_trigger_ci/"
echo "*********************************************************************************"
echo