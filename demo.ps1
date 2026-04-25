Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "?? Self-Healing Infra Demonstration" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Initial State: Checking current pods..." -ForegroundColor Yellow
kubectl get pods -l app=self-healing-app
Write-Host ""

Write-Host "2. Simulating a CPU Spike on the application..." -ForegroundColor Yellow
Write-Host "   -> Sending request to /stress-cpu for 30 seconds"
Start-Job -ScriptBlock { Invoke-RestMethod -Uri "http://localhost:8000/stress-cpu?duration=30" } | Out-Null
Write-Host "   -> Request sent!"
Write-Host ""

Write-Host "3. Waiting for Prometheus to scrape metrics and ML to predict (20s)..." -ForegroundColor Yellow
Start-Sleep -Seconds 20
Write-Host ""

Write-Host "4. Checking ML Anomaly Detector Logs..." -ForegroundColor Yellow
Write-Host "   The Isolation Forest model is analyzing the new CPU data."
$ml_pod = (kubectl get pods -l app=ml-anomaly-detector --no-headers -o custom-columns=":metadata.name")[0]
kubectl logs $ml_pod --tail=5
Write-Host ""

Write-Host "5. Checking Self-Healer Webhook Logs..." -ForegroundColor Yellow
Write-Host "   The healer should receive the alert and scale the deployment."
$healer_pod = (kubectl get pods -l app=self-healer --no-headers -o custom-columns=":metadata.name")[0]
kubectl logs $healer_pod --tail=5
Write-Host ""

Write-Host "6. Final State: Checking pods to see the healing in action..." -ForegroundColor Yellow
Write-Host "   You should see a new self-healing-app pod spinning up!"
Start-Sleep -Seconds 5
kubectl get pods -l app=self-healing-app
Write-Host ""
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "? Demonstration Complete!" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
