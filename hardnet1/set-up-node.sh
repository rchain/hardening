pushd /root/hardening
install --mode=644 hardnet1/node-specific/"$(hostname)"/{environment.docker,rnode.conf} --target-directory=/var/lib/rnode-static/
popd
