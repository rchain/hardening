# Hardening Network
## Setup

1) Set up a shared SSH host to store Terraform state files
    * `cd tfstate`
    * Fill out Terraform variable values in `tfstate/main.tfvars`
        * Currently just `project = "google-cloud-project-id"`
    * Generate a key for the service account `terraform` in Google Cloud and save it as `account.json` file
    * `terraform init` if you're running terraform for the first time
    * `terraform plan`
    * `terraform apply`
