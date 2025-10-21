$ErrorActionPreference = "Stop"

Write-Host "🚀 YouTube to Medium - Cloud Run Deployment Script" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

if (-not $env:PROJECT_ID) {
    Write-Host "❌ Error: PROJECT_ID environment variable not set" -ForegroundColor Red
    Write-Host "   Please run: `$env:PROJECT_ID='your-project-id'" -ForegroundColor Yellow
    exit 1
}

Write-Host "📍 Project ID: $env:PROJECT_ID" -ForegroundColor Green
Write-Host ""

Write-Host "🔧 Enabling required APIs..." -ForegroundColor Yellow
gcloud services enable aiplatform.googleapis.com --project=$env:PROJECT_ID
gcloud services enable generativelanguage.googleapis.com --project=$env:PROJECT_ID
gcloud services enable run.googleapis.com --project=$env:PROJECT_ID
gcloud services enable cloudbuild.googleapis.com --project=$env:PROJECT_ID

Write-Host ""
Write-Host "🏗️  Building and deploying to Cloud Run..." -ForegroundColor Yellow
gcloud run deploy yt2medium `
  --source . `
  --region us-central1 `
  --platform managed `
  --allow-unauthenticated `
  --set-env-vars PROJECT_ID=$env:PROJECT_ID,LOCATION=us-central1 `
  --memory 2Gi `
  --cpu 2 `
  --timeout 300 `
  --max-instances 10 `
  --project=$env:PROJECT_ID

Write-Host ""
Write-Host "✅ Deployment complete!" -ForegroundColor Green
Write-Host ""
Write-Host "🌐 Your app is now live. Access it at the URL shown above." -ForegroundColor Cyan
Write-Host ""
