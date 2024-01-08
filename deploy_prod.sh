#!/bin/bash

# https://stackoverflow.com/questions/19331497/set-environment-variables-from-file-of-key-value-pairs/20909045#20909045
unamestr=$(uname)
if [ "$unamestr" = 'Linux' ]; then
  export $(grep -v '^#' .env | xargs -d '\n')
elif [ "$unamestr" = 'FreeBSD' ] || [ "$unamestr" = 'Darwin' ]; then
  export $(grep -v '^#' .env | xargs -0)
fi

ANSIBLE_CONFIG=ansible/ansible.cfg ansible-playbook ansible/prod/deploy.yml -K -u ubuntu -i ansible/prod/hosts -vvv