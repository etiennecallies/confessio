#!/bin/bash

if [[ $# -eq 0 ]] ; then
    echo 'please specify install, deploy or manage'
    exit 1
fi

source .env;

# In case of manage, we store the django command in EXTRA_COMMAND variable
NEXT_ARGUMENTS=("${@:2}")
EXTRA_COMMAND=$(IFS=' '; echo "${NEXT_ARGUMENTS[*]}")

ANSIBLE_CONFIG=ansible/ansible.cfg ansible-playbook ansible/prod/$1.yml -K -u ubuntu -i ansible/prod/hosts -vvv --extra-vars '{"extra_command": "'$EXTRA_COMMAND'"}'