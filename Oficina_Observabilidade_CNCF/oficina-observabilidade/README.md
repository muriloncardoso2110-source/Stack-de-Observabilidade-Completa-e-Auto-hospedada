# Oficina de Observabilidade

Laboratório local de métricas, logs distribuídos e rastreamento de requisições, com ferramentas open source. O objetivo é aprender a observar uma API de ponta a ponta, identificar erros e validar alertas. Projeto de portfólio para DevOps / SRE júnior–pleno.

## Arquitetura

```text
                      ┌───────────── Grafana ─────────────┐
                      │ dashboards e pesquisa centralizada │
                      └──────────────┬────────────────────┘
                 ┌───────────────────┼────────────────────┐
             Prometheus             Loki                 Tempo
            (métricas)             (logs)               (traces)
                 ▲                   ▲                     ▲
                 │                   └─────┬───────────────┘
                 │                 OTel Collector
                 │                   ▲    ▲
                 │           logs JSON    traces OTLP/HTTP
                 └─────────────── API Python
                        /metrics (scrape)

Prometheus → Alertmanager → alertas exibidos localmente
```

A aplicação registra métricas Prometheus e produz logs JSON e traces no formato OTLP. O OpenTelemetry Collector encaminha logs ao Loki e traces ao Tempo. Grafana apresenta tudo; Prometheus envia alertas para o Alertmanager. Nada depende de SaaS.

## Pré-requisitos

- Windows 10/11 com **Docker Desktop** (Linux containers + WSL2), ou Linux/macOS com Docker Engine e Docker Compose v2.
- Recomenda-se **8 GB RAM ou mais** no computador; reserve cerca de 4 GB ao Docker e espaço em disco para imagens e dados.
- Portas locais disponíveis: **3000, 8080, 9090, 9093**.
- PowerShell no Windows. Não precisa instalar Python local para usar o laboratório.

## Instalação no Windows (a partir do zero)

1. Instale Docker Desktop: https://docs.docker.com/desktop/setup/install/windows-install/ . Reinicie, se solicitado, e espere a indicação de que o Docker está rodando.
2. Extraia este projeto e abra a **pasta extraída** no VS Code.
3. Abra o terminal PowerShell do VS Code (Terminal → New Terminal).
4. Execute:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\iniciar.ps1
```

5. Na primeira execução é criado `.env`. Defina ali sua senha local em `GRAFANA_ADMIN_PASSWORD` (não publique esse arquivo). Caso altere a senha depois do Grafana já ter criado o banco, a senha existente continuará valendo; redefina pelo Grafana CLI, se necessário.
6. Aguarde os containers ficarem prontos e veja o status com `docker compose ps`. Para erros de inicialização, utilize `docker compose logs --tail 100 nome-do-servico`.

Alternativa (Linux/macOS ou terminal comum):

```bash
cp .env.example .env
# ajuste a senha em .env
docker compose up -d --build
```

## Endereços

| Serviço | Endereço | Observação |
|---|---|---|
| Grafana | http://localhost:3000 | Login definido no `.env` |
| API de exemplo | http://localhost:8080 | Endpoints abaixo |
| Prometheus | http://localhost:9090/targets | Verifique `oficina-api: UP` |
| Alertmanager | http://localhost:9093 | Alertas ativos |

Loki, Tempo e OTel Collector só aceitam conexões pela rede interna do Compose.

## Primeiro teste

No PowerShell:

```powershell
.\scripts\testar.ps1
```

Ou faça manualmente:

- `http://localhost:8080/` retorna a identificação da aplicação.
- `http://localhost:8080/health` retorna `{ "status": "ok" }`.
- `http://localhost:8080/api/pedido` gera uma requisição normal.
- `http://localhost:8080/api/lento` simula latência de ~800 ms.
- `http://localhost:8080/api/erro` retorna erro 500 **de propósito**.
- `http://localhost:8080/metrics` expõe métricas Prometheus.

**Métricas:** abra Grafana → Dashboards → Observabilidade → **Oficina | Visão geral**. É necessário gerar tráfego para aparecerem séries de requisições. As métricas são coletadas a cada 10 segundos.

**Logs:** Grafana → Explore → selecione **Loki**; execute `{service_name="oficina-api"}`. Se a consulta não retornar linhas, aguarde o batch do Collector e confira `docker compose logs otel-collector`. Dependendo da normalização de atributos do Loki, consulte também o seletor de labels na interface.

**Traces:** Grafana → Explore → **Tempo** → Search, filtrando `service.name = oficina-api`; gere algumas chamadas e aguarde o envio. Você também pode consultar um trace pelo `trace-id` retornado no cabeçalho HTTP, desde que o envio do Collector tenha ocorrido.

**Alertas:** em Prometheus → Alerts, veja as regras cadastradas. Para simular indisponibilidade, rode `docker compose stop app`, espere pelo menos 40 segundos e veja Alertmanager. Recupere com `docker compose start app`. Para testar a taxa de erros, gere vários acessos a `/api/erro` durante mais de um minuto.

## Arquivos do projeto

```text
app/                   API de laboratório, Dockerfile e métricas
config/                Prometheus, alertas, Loki, Tempo e OTel Collector
grafana/               Data sources e dashboard provisionados automaticamente
scripts/               Iniciar, testar, parar e limpar no PowerShell
tests/                 Testes unitários
.github/workflows/      Validação por GitHub Actions
docker-compose.yml      Orquestração local
```

## Rotina operacional

```powershell
# Verificar containers
docker compose ps
# Ver logs do coletor
docker compose logs -f --tail 100 otel-collector
# Desligar mantendo métricas, logs e dashboards
.\scripts\parar.ps1
# Apagar TODOS os dados persistidos (pede confirmação)
.\scripts\limpar-tudo.ps1
```

## Diagnóstico rápido

- **Conflito de porta:** pare a aplicação que usa 3000/8080/9090/9093 ou altere a porta à esquerda no `docker-compose.yml`.
- **Grafana não abre:** cheque `docker compose ps` e `docker compose logs grafana`.
- **Prometheus não vê a API:** confira `/health`, `/metrics`, o container `app` e `/targets`.
- **Nenhum log:** cheque o volume `app_logs` e `docker compose logs otel-collector`; a primeira importação pode levar alguns segundos.
- **Traces ausentes:** verifique o endpoint OTLP configurado na aplicação e os logs de `otel-collector` e `tempo`.
- **Windows:** mantenha Docker Desktop iniciado; use containers Linux, não Windows.

## Escopo e limites

Ambiente de **aprendizado local**, sem autenticação entre os serviços internos, TLS, alta disponibilidade, backup remoto ou retenção de produção. Os serviços web estão vinculados a `127.0.0.1` e não devem ser expostos diretamente à internet. A senha de exemplo deve ser alterada. Loki e Tempo usam armazenamento local; não são serviços gerenciados. Para ambientes reais, seriam necessários controles de acesso, políticas de retenção, backups, segurança e dimensionamento.

## Melhorias possíveis

- Notificações externas do Alertmanager (e-mail ou Teams) com segredos armazenados fora do repositório.
- Integração com Kubernetes, métricas de nós e `kube-state-metrics`.
- Instrumentação automática com bibliotecas OpenTelemetry e propagação de contexto entre serviços.

## Referências técnicas

- https://opentelemetry.io/docs/collector/
- https://prometheus.io/docs/introduction/overview/
- https://grafana.com/docs/loki/latest/
- https://grafana.com/docs/tempo/latest/
- https://grafana.com/docs/grafana/latest/
