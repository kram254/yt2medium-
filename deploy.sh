#!/bin/bash

set -e

echo "🚀 YouTube to Medium - Cloud Run Deployment Script"
echo "=================================================="
echo ""

if [ -z "$PROJECT_ID" ]; then
    echo "❌ Error: PROJECT_ID environment variable not set"
    echo "   Please run: export PROJECT_ID=your-project-id"
    exit 1
fi

echo "📍 Project ID: $PROJECT_ID"
echo ""

echo "🔧 Enabling required APIs..."
gcloud services enable aiplatform.googleapis.com --project=$PROJECT_ID
gcloud services enable generativelanguage.googleapis.com --project=$PROJECT_ID
gcloud services enable run.googleapis.com --project=$PROJECT_ID
gcloud services enable cloudbuild.googleapis.com --project=$PROJECT_ID

echo ""
echo "🏗️  Building and deploying to Cloud Run..."
gcloud run deploy yt2medium \
  --source . \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars PROJECT_ID=$PROJECT_ID,LOCATION=us-central1 \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --max-instances 10 \
  --project=$PROJECT_ID

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🌐 Your app is now live. Access it at the URL shown above."
echo ""
