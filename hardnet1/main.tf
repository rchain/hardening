terraform {
  backend "gcs" {
    bucket  = "rchain-terraform-state"
    prefix  = "hardnet1"
    credentials = "account.json"
  }
}

variable "resources_name" { default = "hardnet1" }
variable "gcp_zone" { default = "europe-north1-a" }
variable "node_count" { default = 2 }

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
    content      = "${file("set-up-instance.sh")}"
  }

  part {
    filename     = "rchain-sre-git-crypt-key.b64"
    content_type = "text/x-shellscript"
    content      = "${file("rchain-sre-git-crypt-key.b64")}"
  }

  part {
    filename     = "environment.docker"
    content_type = "text/x-shellscript"
    content      = "${file("node-specific/node${count.index}/environment.docker")}"
  }

  part {
    filename     = "rnode.conf"
    content_type = "text/x-shellscript"
    content      = "${file("node-specific/node${count.index}/rnode.conf")}"
  }
}


locals {
  node_cloudinit_config = {
    "0" = "${data.template_cloudinit_config.node.0.rendered}"
    "1" = "${data.template_cloudinit_config.node.1.rendered}"
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
