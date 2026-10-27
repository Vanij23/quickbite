# QuickBite - Cloud DevOps Capstone

Food-ordering app delivered end to end with AWS and DevOps practices.

```
Developer -> GitHub -> GitHub Actions (test, build, push) -> ECR -> ECS Fargate -> ALB -> Users
                                  |                                   |
                         OIDC role (no keys)            DynamoDB, CloudWatch, CloudTrail, VPC
```

| Layer | Choice |
|---|---|
| App | Flask + gunicorn, orders in DynamoDB |
| Container | Docker (non-root), Amazon ECR with scan on push |
| Run | ECS Fargate in private subnets, ALB in public subnets, auto scaling 1-3 tasks |
| CI/CD | GitHub Actions: pytest, docker build, push to ECR, new task definition, deploy, verify |
| IaC | CloudFormation (`infra/quickbite.yaml`) + AWS CLI scripts (`scripts/`) |
| Monitoring | CloudWatch dashboard, 4 alarms, SNS email, Container Insights |
| Logging | App logs to CloudWatch Logs (JSON), VPC flow logs (rejected traffic) |
| Auditing | CloudTrail (S3 + CloudWatch Logs, log validation), unauthorized-call alarm |
| Security | Least-privilege IAM, OIDC instead of access keys, SG chaining, private tasks, encrypted S3/DynamoDB |

## Repo layout

```
app/        Flask app, tests, Dockerfile
infra/      quickbite.yaml  (CloudFormation)
scripts/    deploy.sh status.sh scale.sh audit.sh loadtest.sh teardown.sh
.github/    workflows/ci-cd.yml
```

## Runbook

Use **AWS CloudShell** (AWS console, top bar): it already has the AWS CLI, Docker and git. Pick one region
(e.g. `ap-south-1`) and stay in it.

1. **Push this repo to GitHub** (a repo you own, branch `main`), e.g. `vanij/quickbite`.
2. **Deploy the stack** in CloudShell:
   ```bash
   git clone https://github.com/<you>/quickbite.git && cd quickbite
   ./scripts/deploy.sh you@example.com <you>/quickbite
   ```
   If it fails with "provider already exists", re-run with `false` as the 3rd argument.
   Takes about 8-10 minutes. It prints the app URL, the role ARN and the region.
3. **Confirm the SNS email** that AWS sends to your address (otherwise alarms never reach you).
4. **Connect GitHub to AWS**: repo -> Settings -> Secrets and variables -> Actions -> *Variables*:
   - `AWS_ROLE_ARN` = the role ARN printed by deploy.sh
   - `AWS_REGION` = your region
5. **Pipeline demo**: edit a menu item in `app/app.py` (e.g. add `{"id": 5, "name": "Cold Coffee", "price": 99}`)
   and update the matching count in `app/test_app.py` if needed, commit, push to `main`. Watch the Actions run,
   then refresh the app URL: the footer shows the new commit id and the new item appears.
6. **Evidence scripts**: `./scripts/status.sh`, `./scripts/loadtest.sh`, `./scripts/scale.sh 2`, `./scripts/audit.sh`.
7. **Clean up when finished**: `./scripts/teardown.sh` (the NAT gateway costs money while it exists).

## Notes and known limits

- HTTP only: HTTPS needs a domain name and an ACM certificate (listed as future work).
- Pipeline deployments register new task-definition revisions outside CloudFormation. Re-running
  `deploy.sh` later is safe because the template keeps using the `latest` tag that the pipeline also pushes.
- Cost while running is roughly the NAT gateway plus ALB plus one small Fargate task (a few US cents per hour).
  Delete the stack after the demo.
