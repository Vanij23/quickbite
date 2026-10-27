#!/usr/bin/env bash
# Generates traffic so CPU rises, auto scaling reacts and the dashboard shows activity.
# Usage: ./scripts/loadtest.sh [seconds=180] [parallel=30]
set -euo pipefail
DURATION="${1:-180}"
PAR="${2:-30}"
STACK="${STACK_NAME:-quickbite}"
REGION="${AWS_REGION:-${AWS_DEFAULT_REGION:-$(aws configure get region)}}"
URL="$(aws cloudformation describe-stacks --region "$REGION" --stack-name "$STACK" \
  --query "Stacks[0].Outputs[?OutputKey=='AppUrl'].OutputValue" --output text)"

echo "Hitting $URL with $PAR parallel workers for ${DURATION}s..."
END=$(( $(date +%s) + DURATION ))
worker() { while [ "$(date +%s)" -lt "$END" ]; do
  curl -s -o /dev/null "$URL/api/menu"
  curl -s -o /dev/null -X POST "$URL/api/orders" -H 'Content-Type: application/json' \
    -d '{"customer":"loadtest","items":[{"id":1,"qty":1}]}'
done; }
for _ in $(seq "$PAR"); do worker & done
wait
echo "Load test finished. Check the CloudWatch dashboard and 'scripts/status.sh'."
