pushd /root/hardening
install --mode=644 hardnet1/node-specific/"$(hostname)"/{wallets.txt,rnode.conf,bonds.txt} --target-directory=/var/lib/rnode-static/
popd
