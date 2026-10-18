Set-Location (Join-Path $PSScriptRoot '..')
Write-Host 'ATENCAO: este comando APAGA dados historicos de metricas, logs, traces e Grafana.'
$confirmacao = Read-Host 'Digite APAGAR para continuar'
if ($confirmacao -ceq 'APAGAR') { docker compose down --volumes } else { Write-Host 'Operacao cancelada.' }
