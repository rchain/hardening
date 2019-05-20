apt_update: true
apt_upgrade: true
packages:
 - unzip

users:
  - name: terraform
    ssh_authorized_keys:
      - ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAICR/qyFGuF5YkptuO1KP25Y9qGZAWAAE8QAC2oHK+17N tomas@pyrofex.net
      - ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAID2siYwsBrvHlJfLqACH+UPeD7BumqC+QDYNATltRltp adam.szkoda@rchain.coop
