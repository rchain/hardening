# Hardening Network
## Setup

1) Set up a shared SSH host to store Terraform state files
    * `cd tfstate`
    * Generate a key for the service account `terraform` in Google Cloud and save it as `account.json` file
    * `terraform init` if you're running terraform for the first time
    * `terraform plan`
    * `terraform apply`

Warning: The cloud-init script gets executed only once, when the GCP instance
         gets created.  So if there are any changes made to the cloud-init
         script that need to be applied, use `terraform taint
         google_compute_instance.INSTANCE_NAME` and then `terraform apply`.
         `terraform apply` alone won't work!

`tail -f /var/log/cloud-init-output.log` can be used to see when cloud-init finished job.

2) Prepare a repository on the `tfstate` machine for use with Terraform:

    * Copy the git-crypt key file onto the machine: `gcloud compute scp --project "developer-222401" --zone "europe-north1-a" rchain-sre-git-crypt-key terraform@tfstate:`
    * SSH onto the machine: `gcloud compute ssh --project "developer-222401" --zone "europe-north1-a" terraform@tfstate`
    * Decrypt the repository: `cd hardening; git-crypt unlock ~/rchain-sre-git-crypt-key`
