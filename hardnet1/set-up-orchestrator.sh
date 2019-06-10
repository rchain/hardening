#!/bin/bash -ue

pushd /root/hardening
cp hardnet1/orchestrator.service /etc/systemd/system/orchestrator.service

mkdir -p /root/.ssh
cp hardnet1/id_orchestrator /root/.ssh/

pushd orchestrator
python3 -m pip install pipenv
python3 -m pipenv sync
popd
systemctl daemon-reload
systemctl enable --now orchestrator
popd
