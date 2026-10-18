$ErrorActionPreference = 'Stop'
for ($i = 0; $i -lt 25; $i++) {
 try { $r = Invoke-RestMethod 'http://localhost:8080/health' -TimeoutSec 3; if ($r.status -eq 'ok') { break } } catch { Start-Sleep -Seconds 2 }
}
for ($i = 1; $i -le 25; $i++) { Invoke-RestMethod 'http://localhost:8080/api/pedido' | Out-Null }
try { Invoke-WebRequest 'http://localhost:8080/api/erro' -UseBasicParsing | Out-Null } catch { Write-Host 'Erro HTTP 500 intencional gerado.' }
Invoke-RestMethod 'http://localhost:8080/api/lento' | Out-Null
Write-Host 'Trafego gerado. Consulte Grafana > Dashboards > Observabilidade.'
