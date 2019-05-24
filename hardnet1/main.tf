variable "resources_name" { default = "hardnet1" }
variable "gcp_zone" { default = "europe-north1-a" }
variable "node_count" { default = 1 }

provider "google" {
  project = "developer-222401"
  zone    = "${var.gcp_zone}"
}

provider "google-beta" {
  project = "developer-222401"
  zone    = "${var.gcp_zone}"
}
