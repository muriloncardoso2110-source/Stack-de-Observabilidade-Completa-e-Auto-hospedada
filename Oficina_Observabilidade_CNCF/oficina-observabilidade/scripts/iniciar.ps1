$ErrorActionPreference = 'Stop'
Set-Location (Join-Path $PSScriptRoot '..')
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) { throw 'Docker nao encontrado. Instale Docker Desktop e abra o aplicativo.' }
docker info | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'Docker Desktop nao esta em execucao.' }
if (-not (Test-Path '.env')) { Copy-Item '.env.example' '.env'; Write-Host 'Arquivo .env criado. Altere a senha do Grafana antes de compartilhar a maquina.' }
docker compose config --quiet
if ($LASTEXITCODE -ne 0) { throw 'Configuracao do Compose invalida.' }
docker compose up -d --build
if ($LASTEXITCODE -ne 0) { throw 'Falha ao iniciar os containers. Verifique docker compose logs.' }
Write-Host 'Grafana: http://localhost:3000 | API: http://localhost:8080 | Prometheus: http://localhost:9090 | Alertmanager: http://localhost:9093'
