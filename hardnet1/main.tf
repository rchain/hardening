terraform {
  backend "gcs" {
    bucket  = "rchain-terraform-state"
    prefix  = "hardnet1"
    credentials = "account.json"
  }
}

variable "resources_name" { default = "hardnet1" }
variable "gcp_zone" { default = "europe-north1-a" }
variable "node_count" { default = 1 }

provider "google" {
  project = "developer-222401"
  zone    = "${var.gcp_zone}"
  credentials = "${file("account.json")}"
}

provider "google-beta" {
  project = "developer-222401"
  zone    = "${var.gcp_zone}"
  credentials = "${file("account.json")}"
}


resource "google_service_account" "svc_account_node" {
  account_id = "${var.resources_name}-node"
}

resource "google_storage_bucket_iam_member" "member" {
  bucket = "heapdumps.bucket.rchain-dev.tk"
  role = "roles/storage.objectCreator"
  member = "serviceAccount:${google_service_account.svc_account_node.email}"
}


data "template_cloudinit_config" "orchestrator" {
  gzip          = false
  base64_encode = false

  part {
    filename     = "cloud-config.yaml"
    content_type = "text/cloud-config"
    content      = "${file("cloud-config.yaml")}"
  }

  part {
    filename     = "set-up.sh"
    content_type = "text/x-shellscript"
    content      = "${file("set-up-instance.sh")} ${file("set-up-orchestrator.sh")}"
  }

  part {
    filename     = "part-handler.py"
    content_type = "text/part-handler"
    content      = "${file("part-handler.py")}"
  }

  part {
    filename     = "/root/rchain-sre-git-crypt-key"
    content_type = "application/base64"
    content      = "${file("rchain-sre-git-crypt-key.b64")}"
  }
}


data "template_cloudinit_config" "bootstrap" {
  gzip          = false
  base64_encode = false

  part {
    filename     = "cloud-config.yaml"
    content_type = "text/cloud-config"
    content      = "${file("cloud-config.yaml")}"
  }

  part {
    filename     = "set-up.sh"
    content_type = "text/x-shellscript"
    content      = "${file("set-up-instance.sh")} ${file("set-up-bootstrap.sh")}"
  }

  part {
    filename     = "part-handler.py"
    content_type = "text/part-handler"
    content      = "${file("part-handler.py")}"
  }

  part {
    filename     = "/root/rchain-sre-git-crypt-key"
    content_type = "application/base64"
    content      = "${file("rchain-sre-git-crypt-key.b64")}"
  }
}


data "template_cloudinit_config" "node" {
  count = "${var.node_count}"

  gzip          = false
  base64_encode = false

  part {
    filename     = "cloud-config.yaml"
    content_type = "text/cloud-config"
    content      = "${file("cloud-config.yaml")}"
  }

  part {
    filename     = "set-up-instance.sh"
    content_type = "text/x-shellscript"
    content      = "${file("set-up-instance.sh")} ${file("set-up-node.sh")}"
  }

  part {
    filename     = "part-handler.py"
    content_type = "text/part-handler"
    content      = "${file("part-handler.py")}"
  }

  part {
    filename     = "/root/rchain-sre-git-crypt-key"
    content_type = "application/base64"
    content      = "${file("rchain-sre-git-crypt-key.b64")}"
  }
}


locals {
  node_cloudinit_config = {
    "0" = "${data.template_cloudinit_config.node.0.rendered}"
  }
}


resource "google_compute_instance" "orchestrator" {
  name = "${var.resources_name}-orchestrator"

  # Nonstandard amount of RAM
  machine_type =  "n1-standard-1"

  metadata {
    user-data = "${data.template_cloudinit_config.orchestrator.rendered}"
  }

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-1810"
      size = 160
      type = "pd-standard"
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
}


resource "google_compute_instance" "bootstrap" {
  name = "${var.resources_name}-bootstrap"

  # Nonstandard amount of RAM
  machine_type = "custom-4-16384"

  metadata {
    user-data = "${data.template_cloudinit_config.bootstrap.rendered}"
  }

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
}


resource "google_compute_instance" "node" {
  count = "${var.node_count}"
  name = "${var.resources_name}-node${count.index}"

  # Nonstandard amount of RAM
  machine_type = "custom-4-16384"

  metadata {
    user-data = "${local.node_cloudinit_config[count.index]}"
  }

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
}
