#!/usr/bin/env bash
# One-shot deploy: create/update the CloudFormation stack, push the first image, start the service.
# Run from AWS CloudShell (has AWS CLI + Docker) or any machine with both installed.
#
# Usage: ./scripts/deploy.sh <alert-email> <github-owner/repo> [create-oidc-provider: true|false]
set -euo pipefail

EMAIL="${1:?usage: deploy.sh <alert-email> <github-owner/repo> [true|false]}"
REPO="${2:?usage: deploy.sh <alert-email> <github-owner/repo> [true|false]}"
CREATE_OIDC="${3:-true}"
STACK="${STACK_NAME:-quickbite}"
REGION="${AWS_REGION:-${AWS_DEFAULT_REGION:-$(aws configure get region)}}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

deploy_stack() {  # $1 = DesiredCount
  aws cloudformation deploy \
    --region "$REGION" \
    --stack-name "$STACK" \
    --template-file "$ROOT/infra/quickbite.yaml" \
    --capabilities CAPABILITY_NAMED_IAM \
    --no-fail-on-empty-changeset \
    --parameter-overrides \
      AlertEmail="$EMAIL" GitHubRepo="$REPO" \
      CreateOidcProvider="$CREATE_OIDC" DesiredCount="$1"
}

output() {
  aws cloudformation describe-stacks --region "$REGION" --stack-name "$STACK" \
    --query "Stacks[0].Outputs[?OutputKey=='$1'].OutputValue" --output text
}

echo "==> [1/4] Creating infrastructure (VPC, ECR, ECS, ALB, DynamoDB, monitoring, CloudTrail)"
deploy_stack 0

REPO_URI="$(output EcrRepositoryUri)"
echo "==> [2/4] Building and pushing the first image to $REPO_URI"
aws ecr get-login-password --region "$REGION" | docker login --username AWS --password-stdin "${REPO_URI%%/*}"
SHA="$(git -C "$ROOT" rev-parse HEAD 2>/dev/null || echo initial)"
docker build -t "$REPO_URI:latest" -t "$REPO_URI:$SHA" "$ROOT/app"
docker push "$REPO_URI:latest"
docker push "$REPO_URI:$SHA"

echo "==> [3/4] Starting the service (DesiredCount=1)"
deploy_stack 1
aws ecs wait services-stable --region "$REGION" \
  --cluster "$(output ClusterName)" --services "$(output ServiceName)"

echo "==> [4/4] Done"
URL="$(output AppUrl)"
echo "App URL          : $URL"
echo "GitHub role ARN  : $(output GitHubDeployRoleArn)   (save as repo variable AWS_ROLE_ARN)"
echo "Region           : $REGION                          (save as repo variable AWS_REGION)"
echo "Health check     : $(curl -fsS "$URL/health" || echo 'not ready yet')"
echo "REMINDER: confirm the SNS subscription email sent to $EMAIL, or alarms will not be delivered."
