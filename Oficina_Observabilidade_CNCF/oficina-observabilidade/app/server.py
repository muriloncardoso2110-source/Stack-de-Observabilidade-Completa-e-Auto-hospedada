"""API de exemplo para o laboratório de observabilidade (sem dependências externas)."""
import json
import os
import random
import threading
import time
import urllib.request
import uuid
from collections import Counter
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

START = time.monotonic()
LOCK = threading.Lock()
REQUESTS = Counter()
DURATION = Counter()
BUCKETS = (0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5)
HIST = Counter()
LOG_PATH = Path(os.getenv('LOG_FILE', '/tmp/oficina-app.jsonl'))
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
SERVICE = 'oficina-api'


def log(level, message, **fields):
    row = {'timestamp': datetime.now(timezone.utc).isoformat(), 'level': level,
           'service': SERVICE, 'message': message, **fields}
    line = json.dumps(row, ensure_ascii=False)
    with LOCK:
        with LOG_PATH.open('a', encoding='utf-8') as fh:
            fh.write(line + '\n')
    print(line, flush=True)


def trace(path, method, status, started, duration, trace_id):
    endpoint = os.environ.get('OTEL_ENDPOINT')
    if not endpoint:
        return
    nano = int(started * 1_000_000_000)
    attributes = [{'key': 'http.route', 'value': {'stringValue': path}},
                  {'key': 'http.request.method', 'value': {'stringValue': method}},
                  {'key': 'http.response.status_code', 'value': {'intValue': str(status)}}]
    body = {'resourceSpans': [{'resource': {'attributes': [
        {'key': 'service.name', 'value': {'stringValue': SERVICE}},
        {'key': 'service.version', 'value': {'stringValue': '1.0.0'}}]},
        'scopeSpans': [{'scope': {'name': 'oficina.manual-instrumentation'}, 'spans': [{
            'traceId': trace_id, 'spanId': uuid.uuid4().hex[:16], 'name': f'{method} {path}',
            'kind': 2, 'startTimeUnixNano': str(nano),
            'endTimeUnixNano': str(nano + int(duration * 1_000_000_000)),
            'attributes': attributes, 'status': {'code': 2 if status >= 500 else 1}}]}]}]}
    payload = json.dumps(body).encode()
    request = urllib.request.Request(endpoint, payload, {'Content-Type': 'application/json'}, 'POST')
    try:
        urllib.request.urlopen(request, timeout=1).close()
    except Exception as exc:
        log('warn', 'Não foi possível exportar o trace', error=str(exc))


def metrics():
    lines = ['# HELP oficina_http_requests_total Total de requisições HTTP',
             '# TYPE oficina_http_requests_total counter']
    with LOCK:
        requests = dict(REQUESTS)
        durations = dict(DURATION)
        hist = dict(HIST)
    for (route, status), count in sorted(requests.items()):
        lines.append(f'oficina_http_requests_total{{route="{route}",status="{status}"}} {count}')
    lines += ['# HELP oficina_http_request_duration_seconds Duração das requisições',
              '# TYPE oficina_http_request_duration_seconds histogram']
    for route in sorted({k[0] for k in requests}):
        for bucket in BUCKETS:
            lines.append(f'oficina_http_request_duration_seconds_bucket{{route="{route}",le="{bucket}"}} {sum(n for (r,b),n in hist.items() if r == route and b <= bucket)}')
        lines.append(f'oficina_http_request_duration_seconds_bucket{{route="{route}",le="+Inf"}} {sum(n for (r,s),n in requests.items() if r == route)}')
        lines.append(f'oficina_http_request_duration_seconds_sum{{route="{route}"}} {durations.get(route,0):.6f}')
        lines.append(f'oficina_http_request_duration_seconds_count{{route="{route}"}} {sum(n for (r,s),n in requests.items() if r == route)}')
    lines += ['# HELP oficina_uptime_seconds Tempo desde a inicialização',
              '# TYPE oficina_uptime_seconds gauge',
              f'oficina_uptime_seconds {time.monotonic()-START:.3f}']
    return '\n'.join(lines) + '\n'


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlsplit(self.path).path
        if path == '/metrics':
            self.send_response(200)
            body = metrics().encode()
            self.send_header('Content-Type', 'text/plain; version=0.0.4; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        started = time.time()
        trace_id = uuid.uuid4().hex
        route = path if path in ('/', '/health', '/api/pedido', '/api/erro', '/api/lento') else '/not-found'
        status = 200
        if path == '/':
            payload = {'projeto': 'Oficina de Observabilidade', 'versao': '1.0.0',
                       'rotas': ['/health', '/api/pedido', '/api/erro', '/api/lento', '/metrics']}
        elif path == '/health':
            payload = {'status': 'ok'}
        elif path == '/api/pedido':
            time.sleep(random.uniform(0.02, 0.12))
            payload = {'pedido': uuid.uuid4().hex[:8], 'status': 'recebido'}
        elif path == '/api/lento':
            time.sleep(0.8)
            payload = {'status': 'processado', 'observacao': 'latencia intencional'}
        elif path == '/api/erro':
            status = 500
            payload = {'erro': 'Falha simulada para testes de alertas'}
        else:
            status = 404
            payload = {'erro': 'Rota não encontrada'}
        body = json.dumps(payload, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('trace-id', trace_id)
        self.end_headers()
        self.wfile.write(body)
        duration = time.time() - started
        with LOCK:
            REQUESTS[(route, str(status))] += 1
            DURATION[route] += duration
            for bucket in BUCKETS:
                if duration <= bucket:
                    HIST[(route, bucket)] += 1
        log('error' if status >= 500 else 'info', 'HTTP request', route=route, status=status,
            duration_ms=round(duration*1000, 1), trace_id=trace_id)
        trace(route, 'GET', status, started, duration, trace_id)

    def log_message(self, *args):
        return


if __name__ == '__main__':
    log('info', 'Servidor iniciado', port=int(os.getenv('PORT', '8080')))
    ThreadingHTTPServer(('0.0.0.0', int(os.getenv('PORT', '8080'))), Handler).serve_forever()
