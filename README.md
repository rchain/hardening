# Hardening Network

1. Terraform relies on a service account named `terraform`.  In case it gets
   deleted somehow, it requires a minimum set of permissions:
    * Compute Admin
    * Security Admin
    * Service Account Admin
    * Service Account User
    * Project IAM Admin
    * Storage Object Admin
2. Terraform also stores its state in a GCP bucket named
   `rchain-terraform-state`.  In case it gets deleted, remember to enable
   versioning for it (`gsutil versioning set on gs://rchain-terraform-state`).
3. `cd hardnet1`
4. Copy `rchain-sre-git-crypt-key` to the current directory
5. The git-crypt key needs to be base64 encoded for transport: `base64 <rchain-sre-git-crypt-key >rchain-sre-git-crypt-key.b64`
6. `terraform init`
7. `terraform plan`
8. `terraform apply`

**Warning!** The cloud-init script gets executed only once, when the GCP instance
gets created.  So if there are any changes made to the cloud-init script that
need to be applied, use `terraform taint
google_compute_instance.INSTANCE_NAME` and then `terraform apply`.  `terraform
apply` alone won't work!

`tail -f /var/log/cloud-init-output.log` can be used to see when cloud-init finished job.

## Development Workflow

In order to avoid repeated deployments via Terraform,
[Mutagen](https://mutagen.io/) can be used to mirror changes made to a
developer-local repository clone, onto the cloud instance running the
Orchestrator:

In `~/.ssh/config`:

```
Host ORCHESTRATOR_INSTANCE_EXTERNAL_IP orchestrator
    HostName ORCHESTRATOR_INSTANCE_EXTERNAL_IP
    User root
    IdentityFile PATH_TO_ID_ORCHESTRATOR_PRIVATE_KEY_FILE
```

```
$ cd orchestrator
$ mutagen create --sync-mode=one-way-replica --default-file-mode=0666 . root@$(gce-get-external-ip hardnet1-orchestrator):/root/hardening/orchestrator
$ mutagen monitor
```

In another window:

```
$ gcloud compute --project "developer-222401" ssh --zone "europe-north1-a" "hardnet1-orchestrator" -- journalctl -fu orchestrator
```

Synchronized changes to the Orchestrator source code won't take effect until it is restarted:

```
$ gcloud compute --project "developer-222401" ssh --zone "europe-north1-a" "hardnet1-orchestrator" -- sudo systemctl restart orchestrator
```
