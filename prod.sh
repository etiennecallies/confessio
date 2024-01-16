#!/bin/bash

if [[ $# -eq 0 ]] ; then
    echo 'please specify install or deploy'
    exit 1
fi

source .env;
ANSIBLE_CONFIG=ansible/ansible.cfg ansible-playbook ansible/prod/$1.yml -K -u ubuntu -i ansible/prod/hosts -vvv