#! /bin/bash

echo "Build docker"
docker build -t nvos/unitest-docker:1.0 -f unittests/Dockerfile .
if [ $? -eq 0 ]
then
        docker run --rm -ti nvos/unitest-docker:1.0
        exit $?
else
        echo "Failed to build the docker"
        exit $?
fi
