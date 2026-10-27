#!/usr/bin/env bash
# Snapshot of the whole environment using only AWS CLI calls (resource management evidence).
set -euo pipefail
STACK="${STACK_NAME:-quickbite}"
REGION="${AWS_REGION:-${AWS_DEFAULT_REGION:-$(aws configure get region)}}"
OUT() { aws cloudformation describe-stacks --region "$REGION" --stack-name "$STACK" \
  --query "Stacks[0].Outputs[?OutputKey=='$1'].OutputValue" --output text; }

CLUSTER="$(OUT ClusterName)"; SERVICE="$(OUT ServiceName)"

echo "=== CloudFormation stack ==="
aws cloudformation describe-stacks --region "$REGION" --stack-name "$STACK" \
  --query "Stacks[0].{Status:StackStatus,Created:CreationTime,Updated:LastUpdatedTime}" --output table

echo "=== ECS service ==="
aws ecs describe-services --region "$REGION" --cluster "$CLUSTER" --services "$SERVICE" \
  --query "services[0].{Status:status,Desired:desiredCount,Running:runningCount,TaskDef:taskDefinition}" --output table

echo "=== Target health (ALB) ==="
TG="$(aws cloudformation describe-stack-resources --region "$REGION" --stack-name "$STACK" \
  --logical-resource-id TargetGroup --query 'StackResources[0].PhysicalResourceId' --output text)"
aws elbv2 describe-target-health --region "$REGION" --target-group-arn "$TG" \
  --query "TargetHealthDescriptions[].{Target:Target.Id,State:TargetHealth.State}" --output table

echo "=== Alarms ==="
aws cloudwatch describe-alarms --region "$REGION" --alarm-name-prefix "$STACK-" \
  --query "MetricAlarms[].{Alarm:AlarmName,State:StateValue}" --output table

echo "=== Images in ECR ==="
aws ecr describe-images --region "$REGION" --repository-name "$STACK" \
  --query "sort_by(imageDetails,&imagePushedAt)[-5:].{Tags:imageTags,Pushed:imagePushedAt}" --output table

echo "=== Live version ==="
curl -fsS "$(OUT AppUrl)/version"; echo
