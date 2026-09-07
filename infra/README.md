# Terraform — SecurePay Platform Infra

Terraform code for SecurePay Platform AWS infrastructure.

## AWS bootstrap (manual, one-time)

Everything below was done by hand through the AWS Console/CLI and is
intentionally not automated with Terraform: the root account, MFA,
and billing controls need to exist before the first apply, not be a
result of running it.

1. AWS account created, root protected by MFA, no root access keys
   exist.
2. Region `mx-central-1` (Mexico Central, Querétaro) enabled under
   Account -> AWS Regions.
3. AWS Budgets configured: zero-spend budget + cost budget with
   $10 / $30 thresholds, email notifications. Set up before the first
   `terraform apply`.
4. IAM user `terraform-admin` created (not root), temporarily granted
   `AdministratorAccess` — narrowed down to least privilege by the
   `iam` module.
5. AWS CLI configured locally under a named profile.

```bash
aws configure --profile securepay
aws sts get-caller-identity --profile securepay
```

All `terraform` / `aws` commands in this project run with
`AWS_PROFILE=securepay`, never through the default profile.

## Layout

Fills in as Phase 4 progresses.

```infra/terraform/
├── modules/          # vpc, iam, kms, rds
└── envs/
    └── dev/          # backend, providers, dev.tfvars
```

## Regions

Primary region is `mx-central-1`.
