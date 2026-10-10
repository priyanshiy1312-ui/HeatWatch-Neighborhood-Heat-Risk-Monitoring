#!/usr/bin/env bash
# Deploy the HeatWatch backend to AWS (needs AWS CLI + SAM CLI, configured credentials).
set -euo pipefail
cd "$(dirname "$0")/.."
rm -rf backend/data && cp -r data backend/data      # ship sample data inside the Lambda package
cd infra
sam build --template-file template.yaml
sam deploy --guided --stack-name heatwatch --capabilities CAPABILITY_IAM
echo "Now: cd ../frontend && VITE_API_URL=<ApiUrl output> npm run build, then upload dist/ (see docs/DEPLOY.md)."
