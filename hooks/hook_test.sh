#!/bin/bash

. ~/.virtualenvs/bagogold/bin/activate

# Verificar branch
BRANCH=$(hg log --template '{branch}' -r $HG_NODE)
BRANCH=${BRANCH:-default}  # set value to 'default' if it was empty

if [ "$BRANCH" == "prod" ] ; then
    python manage.py test --keepdb &> ~/bagogold/output_test.txt
elif [ "$BRANCH" == "hotfix" ] ; then
    python manage.py test --keepdb &> ~/bagogold/output_test.txt
fi
