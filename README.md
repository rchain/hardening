# Hardening Network

1. Terraform relies on a service account named `terraform`.  In case it gets deleted somehow, it requires a minimum set of permissions:
    * Compute Admin
    * Security Admin
    * Service Account Admin
    * Service Account User
    * Project IAM Admin
    * Storage Object Admin
2. `cd hardnet1`
3. `terraform init`
4. `terraform plan`
5. `terraform apply`

**Warning!** The cloud-init script gets executed only once, when the GCP instance
gets created.  So if there are any changes made to the cloud-init script that
need to be applied, use `terraform taint
google_compute_instance.INSTANCE_NAME` and then `terraform apply`.  `terraform
apply` alone won't work!

`tail -f /var/log/cloud-init-output.log` can be used to see when cloud-init finished job.
