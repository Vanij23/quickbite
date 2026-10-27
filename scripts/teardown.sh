#!/usr/bin/env bash
# Delete EVERYTHING this project created, so it stops costing money.
# Run this after the demo is recorded and submitted.
set -euo pipefail
STACK="${STACK_NAME:-quickbite}"
REGION="${AWS_REGION:-${AWS_DEFAULT_REGION:-$(aws configure get region)}}"

BUCKET="$(aws cloudformation describe-stacks --region "$REGION" --stack-name "$STACK" \
  --query "Stacks[0].Outputs[?OutputKey=='TrailBucketName'].OutputValue" --output text)"

echo "Emptying CloudTrail bucket $BUCKET (CloudFormation cannot delete a non-empty bucket)..."
aws s3 rm "s3://$BUCKET" --recursive --region "$REGION" || true

echo "Deleting stack $STACK (this takes a few minutes; the NAT gateway is the slow part)..."
aws cloudformation delete-stack --region "$REGION" --stack-name "$STACK"
aws cloudformation wait stack-delete-complete --region "$REGION" --stack-name "$STACK"
echo "Stack deleted. The GitHub OIDC provider (if created by the stack) was removed with it."
echo "Log groups kept by CloudWatch can be checked with: aws logs describe-log-groups --log-group-name-prefix /ecs/$STACK"
