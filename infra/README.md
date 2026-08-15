# `infra/` — Infrastructure as Code (Terraform)

All AWS infrastructure as code. Nothing gets clicked in the console and left
undocumented — if it exists in AWS, it exists here (charter principle #5).

## Layout

- `terraform/modules/` — reusable modules: `vpc`, `eks`, `iam`, `kms`, `rds`
- `terraform/envs/dev/` — the dev environment (apply → work → **destroy**)

## Discipline

- **Billing first.** AWS Budgets + billing alerts ($10 / $30) go in *before* any
  EKS/NAT is applied (charter money-rule #1).
- **Cost-in-bursts.** `terraform apply` → validate/record demo → `terraform
  destroy`. NAT Gateway and AWS Config tick even while idle — kill them with the
  cluster.
- **State is sensitive.** Remote backend: S3 (versioned, KMS-encrypted, public
  access blocked) + DynamoDB lock. The provider lock file
  (`.terraform.lock.hcl`) **is** committed for reproducible `init`.
- IaC scanning (Checkov, tfsec) runs in pre-commit and CI from Phase 4.

> Status: scaffolded in Phase 0. Implementation lands in Phase 4.
