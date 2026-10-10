# Deploy to AWS

1. In the Bedrock console, open Model access and enable a model (Claude Haiku is cheap). Note its model ID.
2. `./infra/deploy.sh` (answer the guided prompts; pass your email as AlertEmail and your model ID as BedrockModelId).
3. Confirm the SNS email subscription in your inbox.
4. Copy the `ApiUrl` output. Build the frontend:
   `cd frontend && VITE_API_URL=<ApiUrl> npm run build`
5. Host `frontend/dist`: Amplify Hosting (drag and drop the dist folder) is the quickest, or S3 + CloudFront.
6. Test: `curl <ApiUrl>/api/health`, then open the site, pick a ward, press "Send alert to subscribers".

Costs: everything used here is pay-per-use, so a hackathon demo costs cents. Delete the stack afterwards with `sam delete --stack-name heatwatch`.
Note: SMS to Indian numbers needs sender registration, so use email for the demo and mention SMS as the production path.
