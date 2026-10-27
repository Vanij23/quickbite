#!/usr/bin/env bash
# Manually scale the service (demonstrates availability / resource management via the CLI).
# Usage: ./scripts/scale.sh <desired-count 1-3>
set -euo pipefail
COUNT="${1:?usage: scale.sh <1-3>}"
STACK="${STACK_NAME:-quickbite}"
REGION="${AWS_REGION:-${AWS_DEFAULT_REGION:-$(aws configure get region)}}"
OUT() { aws cloudformation describe-stacks --region "$REGION" --stack-name "$STACK" \
  --query "Stacks[0].Outputs[?OutputKey=='$1'].OutputValue" --output text; }

aws ecs update-service --region "$REGION" --cluster "$(OUT ClusterName)" \
  --service "$(OUT ServiceName)" --desired-count "$COUNT" \
  --query "service.{Desired:desiredCount,Running:runningCount}" --output table
aws ecs wait services-stable --region "$REGION" --cluster "$(OUT ClusterName)" --services "$(OUT ServiceName)"
echo "Service is stable at $COUNT task(s)."
