#!/bin/bash

. ./.env; ansible-playbook ansible/prod/deploy.yml -K -u ubuntu -i ansible/prod/hosts -vvv