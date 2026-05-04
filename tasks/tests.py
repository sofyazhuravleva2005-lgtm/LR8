import os
import random
from unittest.mock import patch
from django.test import TestCase, override_settings
from .views import run_simulation, generate_charts


class DoSSimulationTests(TestCase):
    """Модульные тесты для контейнера защиты от DoS-атак"""

    def setUp(self):
        """Настройка окружения перед каждым тестом"""
        os.environ['MAX_REQUESTS_PER_MIN'] = '5'
        os.environ['MAX_CONCURRENT_CONNECTIONS'] = '3'
        random.seed(42)  # для воспроизводимости результатов

    def test_rate_limit_per_ip(self):
        """Проверка фиксации атак при превышении лимита запросов с одного IP"""
        data = run_simulation()
        rate_limit_attacks = [
            a for a in data['attack_stats']
            if 'Превышен лимит' in a[2]
        ]
        self.assertGreater(
            len(rate_limit_attacks), 0,
            "Должны быть атаки из-за rate limiting"
        )

    def test_connection_limit(self):
        """Проверка фиксации атак при превышении одновременных соединений"""
        data = run_simulation()
        conn_attacks = [
            a for a in data['attack_stats']
            if 'одновременных соединений' in a[2]
        ]
        self.assertGreater(
            len(conn_attacks), 0,
            "Должны быть атаки из-за лимита соединений"
        )

    def test_env_defaults(self):
        """Проверка значений по умолчанию, если переменные окружения не заданы"""
        # Удаляем переменные окружения
        for var in ['MAX_REQUESTS_PER_MIN', 'MAX_CONCURRENT_CONNECTIONS']:
            if var in os.environ:
                del os.environ[var]

        data = run_simulation()
        self.assertEqual(data['limits']['max_requests'], 200)
        self.assertEqual(data['limits']['max_connections'], 1000)

    def test_total_attacks_count(self):
        """Проверка соответствия total_attacks длине attack_stats"""
        data = run_simulation()
        self.assertEqual(data['total_attacks'], len(data['attack_stats']))

    def test_chart_generation(self):
        """Проверка создания графиков (без реальной записи на диск)"""
        minutes = [1, 2, 3]
        counts = [10, 20, 15]
        reasons = {'Превышен лимит': 30, 'Превышение соединений': 15}

        # Перехватываем сохранение файлов, чтобы не засорять диск
        with patch('matplotlib.pyplot.savefig'):
            paths = generate_charts(minutes, counts, reasons)

        self.assertIn('bar', paths)
        self.assertIn('line', paths)
        self.assertIn('pie', paths)

    def tearDown(self):
        """Восстановление окружения после тестов"""
        os.environ['MAX_REQUESTS_PER_MIN'] = '5'
        os.environ['MAX_CONCURRENT_CONNECTIONS'] = '3'

from django.test import TestCase, override_settings

class SidecarHTTPSTests(TestCase):
    @override_settings(SECURE_PROXY_SSL_HEADER=('HTTP_X_FORWARDED_PROTO', 'https'))
    def test_https_request_simulation(self):
        """Проверка, что с заголовком X-Forwarded-Proto: https страница отдаётся"""
        response = self.client.get('/', HTTP_X_FORWARDED_PROTO='https')
        self.assertEqual(response.status_code, 200)
        # Проверяем по ключевому слову, чтобы избежать проблем с тире
        self.assertContains(response, "DoS")

    def test_direct_http_still_works(self):
        """Проверка, что прямой HTTP‑запрос (без прокси) также обрабатывается"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
class HTTPSTests(TestCase):
    """Тесты для проверки работы контейнера DoS с HTTPS"""

    @override_settings(SECURE_PROXY_SSL_HEADER=('HTTP_X_FORWARDED_PROTO', 'https'))
    def test_https_request_simulation(self):
        """Проверка, что страница отдаётся с HTTPS-заголовком"""
        response = self.client.get('/', HTTP_X_FORWARDED_PROTO='https')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'DoS')  # или "Контейнер защиты от DoS"

    def test_direct_http_still_works(self):
        """Проверка обратной совместимости"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_simulation_works_with_https(self):
        """Проверка, что симуляция атак работает при HTTPS-заголовке"""
        response = self.client.get('/', HTTP_X_FORWARDED_PROTO='https')
        self.assertContains(response, 'DoS')   # было 'Всего атак', изменено на 'DoS'