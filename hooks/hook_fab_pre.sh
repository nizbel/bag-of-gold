#!/bin/bash

. ~/.virtualenvs/bagogold/bin/activate

# Verificar branch
BRANCH=$(hg log --template '{branch}' -r $HG_NODE)
BRANCH=${BRANCH:-default}  # set value to 'default' if it was empty

if [ "$BRANCH" == "default" ] ; then
    fab dev gerar_css_def
elif [ "$BRANCH" == "hotfix" ] ; then
    fab dev gerar_css_def
fi
