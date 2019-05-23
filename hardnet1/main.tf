variable "resources_name" { default = "hardnet1" }
variable "gcp_zone" { default = "europe-north1-a" }
variable "node_count" { default = 1 }
variable "rchain_sre_git_crypt_key_file" {}

provider "google" {
  project = "developer-222401"
  zone    = "${var.gcp_zone}"
}

provider "google-beta" {
  project = "developer-222401"
  zone    = "${var.gcp_zone}"
}
