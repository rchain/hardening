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


resource "google_compute_instance" "node_host" {
  count = "${var.node_count}"
  name = "${var.resources_name}-node${count.index}"

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
}
