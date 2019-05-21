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

Warning: The cloud-init script gets executed only once, when the GCP instance
         gets created.  So if there are any changes made to the cloud-init
         script that need to be applied, use `terraform taint
         google_compute_instance.INSTANCE_NAME` and then `terraform apply`.
         `terraform apply` alone won't work!
