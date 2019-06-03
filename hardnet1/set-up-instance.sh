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

for file in environment.docker rnode.conf; do
    install --mode=644 /var/lib/cloud/instance/scripts/"$file" --target-directory=/var/lib/rnode-static/
done
