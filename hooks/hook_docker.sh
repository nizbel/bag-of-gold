#!/bin/bash

. ~/.virtualenvs/bagogold/bin/activate

# Verificar branch
BRANCH=$(hg log --template '{branch}' -r $HG_NODE)
BRANCH=${BRANCH:-default}  # set value to 'default' if it was empty

if [ "$BRANCH" == "prod" ] ; then
    docker image build -t nizbel/bagofgold:cron -f Dockercron --add-host=database:172.17.0.1 .
    docker image build -t nizbel/bagofgold:prod -f Dockerprod --add-host=database:172.17.0.1 .
    docker push nizbel/bagofgold:cron
    docker push nizbel/bagofgold:prod
    docker container prune -f
elif [ "$BRANCH" == "hotfix" ] ; then
    docker image build -t nizbel/bagofgold:cron -f Dockercron --add-host=database:172.17.0.1 .
    docker image build -t nizbel/bagofgold:prod -f Dockerprod --add-host=database:172.17.0.1 .
    docker push nizbel/bagofgold:cron
    docker push nizbel/bagofgold:prod
    docker container prune -f
fi
