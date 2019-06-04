#!/bin/bash -ue

mkdir -p /var/lib/rnode-static
chmod 710 /var/lib/rnode-static
chgrp www-data /var/lib/rnode-static

mkdir -p /var/lib/rnode-diag
chmod 750 /var/lib/rnode-diag
chgrp www-data /var/lib/rnode-diag

systemctl restart collectd


mkdir -p /var/lib/rnode-static
chmod 710 /var/lib/rnode-static
chgrp www-data /var/lib/rnode-static

mkdir -p /var/lib/rnode-diag
chmod 750 /var/lib/rnode-diag
chgrp www-data /var/lib/rnode-diag

mkdir -p /mnt/heapdumps
systemctl daemon-reload
systemctl enable --now mnt-heapdumps.mount

if [[ -z "$(docker ps -q -f name='^logspout$')" ]]; then
    docker rm logspout || true
    docker pull gliderlabs/logspout
    docker run -d --restart=unless-stopped --name=logspout -p 8181:80 -v /var/run/docker.sock:/var/run/docker.sock gliderlabs/logspout
fi

systemctl reload sshd

systemctl reload nginx

pushd /root
git clone https://github.com/rchain/hardening.git /root/hardening
base64 --decode </var/lib/cloud/instance/scripts/rchain-sre-git-crypt-key.b64 >rchain-sre-git-crypt-key
cd hardening
git-crypt unlock ../rchain-sre-git-crypt-key
install --mode=644 hardnet1/node-specific/"$(hostname)"/{environment.docker,rnode.conf} --target-directory=/var/lib/rnode-static/
popd
