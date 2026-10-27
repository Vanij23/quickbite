#!/usr/bin/env bash
# Auditing evidence: who did what in the account, straight from CloudTrail via the CLI.
set -euo pipefail
REGION="${AWS_REGION:-${AWS_DEFAULT_REGION:-$(aws configure get region)}}"

echo "=== Last 10 ECS UpdateService calls (the pipeline deployments) ==="
aws cloudtrail lookup-events --region "$REGION" \
  --lookup-attributes AttributeKey=EventName,AttributeValue=UpdateService --max-results 10 \
  --query "Events[].{Time:EventTime,User:Username,Event:EventName}" --output table

echo "=== Last 10 CloudFormation events ==="
aws cloudtrail lookup-events --region "$REGION" \
  --lookup-attributes AttributeKey=EventSource,AttributeValue=cloudformation.amazonaws.com --max-results 10 \
  --query "Events[].{Time:EventTime,User:Username,Event:EventName}" --output table

echo "=== Console sign-ins ==="
aws cloudtrail lookup-events --region "$REGION" \
  --lookup-attributes AttributeKey=EventName,AttributeValue=ConsoleLogin --max-results 5 \
  --query "Events[].{Time:EventTime,User:Username,Event:EventName}" --output table
