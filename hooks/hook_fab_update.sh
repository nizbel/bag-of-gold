#!/bin/bash

. ~/.virtualenvs/bagogold/bin/activate

# Verificar branch
BRANCH=$(hg log --template '{branch}' -r $HG_NODE)
BRANCH=${BRANCH:-default}  # set value to 'default' if it was empty

if [ "$BRANCH" == "default" ] ; then
    fab prod_ec2_support update_ec2
    fab prod_ec2 update_ec2
elif [ "$BRANCH" == "hotfix" ] ; then
    fab prod_ec2_support update_ec2
    fab prod_ec2 update_ec2
fi
