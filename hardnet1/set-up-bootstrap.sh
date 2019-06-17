pushd /root/hardening
install --mode=644 hardnet1/node-specific/"$(hostname)"/rnode.conf --target-directory=/var/lib/rnode-static/
popd
