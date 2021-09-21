#!/bin/bash

argument=${1:-"default_commit_fr_paulg"}
echo "commit comment:" $argument
py -m util.bumpversion
git add .
git commit -m "$argument"
git pull
git push
