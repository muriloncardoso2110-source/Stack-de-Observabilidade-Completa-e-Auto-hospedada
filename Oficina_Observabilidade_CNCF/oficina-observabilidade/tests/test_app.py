import os
import sys
import tempfile
import unittest
from pathlib import Path

os.environ['LOG_FILE'] = str(Path(tempfile.gettempdir()) / 'oficina-test-log.jsonl')
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
import server


class TestesDaApi(unittest.TestCase):
    def test_metricas_expoem_uptime(self):
        self.assertIn('oficina_uptime_seconds', server.metrics())

    def test_metricas_possuem_tipo(self):
        self.assertIn('# TYPE oficina_http_requests_total counter', server.metrics())

    def test_buckets_estao_ordenados(self):
        self.assertEqual(sorted(server.BUCKETS), list(server.BUCKETS))

    def test_log_json(self):
        server.log('info', 'teste', identificador='abc')
        self.assertIn('"identificador": "abc"', Path(os.environ['LOG_FILE']).read_text())


if __name__ == '__main__':
    unittest.main()
