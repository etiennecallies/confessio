#!/bin/bash

. ./.env; ANSIBLE_CONFIG=ansible/ansible.cfg ansible-playbook ansible/prod/deploy.yml -K -u ubuntu -i ansible/prod/hosts -vvv