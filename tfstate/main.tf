provider "google" {
  credentials = "${file("account.json")}"
  project = "${var.project}"
  version = "~> 2.3"
}

data "template_file" "script" {
  template = "${file("${path.module}/cloud-config.yaml.tmpl")}"

  vars {
  }
}

data "template_cloudinit_config" "config" {
  gzip          = false
  base64_encode = false

  part {
    filename     = "cloud-config.txt"
    content_type = "text/cloud-config"
    content      = "${data.template_file.script.rendered}"
  }
}

resource "google_compute_instance" "tfstate" {
  count = 1
  name = "tfstate"
  machine_type = "n1-standard-1"
  zone = "europe-north1-a"

  metadata {
    user-data = "${data.template_cloudinit_config.config.rendered}"
  }

  boot_disk {
    auto_delete = true
    initialize_params {
      image = "ubuntu-1804-lts"
    }
  }

  network_interface {
    network = "default"
    access_config {
    }
  }
}
