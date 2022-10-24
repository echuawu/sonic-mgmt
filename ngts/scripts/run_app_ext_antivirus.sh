#!/bin/bash

die()
{
  echo -e "\e[1;31m $* \e[0m"
  exit 1
}

main()
{
  WJH_URL=$1

  if [ "${WJH_URL}" == "" ]; then
    die "Argument: 'WJH_URL' cannot be empty\nExample: ./run_app_ext_antivirus.sh urm.nvidia.com/sw-nbu-sws-sonic-docker/sonic-wjh:1.3.0-202205-23"
  fi

  WJH_VER=${WJH_URL##*/}
 
  docker_pull_cmd="docker pull ${WJH_URL}"
  docker_save_cmd="docker save ${WJH_URL} > /auto/sysgwork/tmp/sonic-wjh:${WJH_VER}"
  docker_rm_cmd="docker image rm ${WJH_URL}"

  echo -e "\e[1;42m Downloading the docker image \e[0m"
  sshpass -p 'roysr11' ssh -o StrictHostKeyChecking=no roysr@r-build-02 $docker_pull_cmd || die "Failed to pull the docker image"
  echo -e "\e[1;42m Saving the docker image into a tar file \e[0m"
  sshpass -p 'roysr11' ssh -o StrictHostKeyChecking=no roysr@r-build-02 $docker_save_cmd || die "Failed to save the docker image"
  echo -e "\e[1;42m Delete the docker image from the build server \e[0m"
  sshpass -p 'roysr11' ssh -o StrictHostKeyChecking=no roysr@r-build-02 $docker_rm_cmd || die "Failed to remove the docker image"
  echo -e "\e[1;42m Running Antivirus \e[0m"
  /auto/GLIT/SCRIPTS/HELPERS/antivirus-scan.sh /auto/sysgwork/tmp/sonic-wjh:$WJH_VER || die "The antivirus scan has failed, please review the logs!"
  echo -e "\e[1;42m Cleanup the env \e[0m"
  rm -f /auto/sysgwork/tmp/sonic-wjh:$WJH_VER || die "Failed to remove the image from /auto/sysgwork/tmp/"


}

main $*

