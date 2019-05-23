resource "google_compute_instance" "node_host" {
  count = "${var.node_count}"
  name = "${var.resources_name}-node${count.index}"
  hostname = "${var.resources_name}-node${count.index}"

  # Nonstandard amount of RAM
  machine_type = "custom-4-16384"

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-1810"
      size = 160
      type = "pd-ssd"
    }
  }

  tags = [
    "${var.resources_name}-node",
    "collectd-out",
    "elasticsearch-out",
    "logstash-tcp-out",
    "logspout-http"
  ]

  service_account {
    email = "${google_service_account.svc_account_node.email}"
    scopes = [ "https://www.googleapis.com/auth/cloud-platform" ]
  }

  network_interface {
    network = "default"
    access_config {
    }
  }

  connection {
    type = "ssh"
    user = "root"
    private_key = "${file("~/.ssh/google_compute_engine")}"
  }

  provisioner "file" {
    source = "${var.rchain_sre_git_crypt_key_file}"
    destination = "/root/rchain-sre-git-crypt-key"
  }
}
