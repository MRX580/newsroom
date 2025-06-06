from django.test import TestCase, Client
from unittest.mock import patch
from django.urls import reverse
from django.contrib.auth.models import User

class StatsViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('stats_view')
        self.user = User.objects.create_user(username='testuser', password='password')
        self.client.login(username='testuser', password='password')

    @patch('app.views.raw_query')
    def test_get_returns_form(self, mock_raw_query):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<form')

    @patch('app.views.raw_query')
    def test_post_returns_filtered_results(self, mock_raw_query):
        def raw_query_side_effect(sql, params):
            # Главный агрегирующий запрос (main_rows)
            if 'GROUP BY' in sql or 'main_data' in sql or 'COUNT(' in sql:
                return [{
                    "video_id": 42,
                    "title": "Test title",
                    "limit_type": "A",
                    "download_count": 1,
                    "agreement_ids": [100]
                }]
            # agreements для клиентов
            if 'FROM business_agreements' in sql:
                return [
                    {"id": 100, "company_id": 200},
                ]
            # компании
            if 'FROM business_companies' in sql:
                return [
                    {"id": 200, "name": "Компания1"}
                ]
            # теги для видео
            if 'FROM content_tag_connections' in sql:
                return [{"connectable_id": 42, "tag_id": 10}]
            # переводы тегов
            if 'FROM content_tag_translations' in sql:
                return [{"content_tag_id": 10, "name": "Тег1"}]
            return []
        mock_raw_query.side_effect = raw_query_side_effect

        form_data = {
            "publication_from": "2024-01-01",
            "publication_to": "2024-12-31",
            "operation_from": "2024-01-01",
            "operation_to": "2024-12-31",
            "keyword": "Test",
        }
        response = self.client.post(self.url, form_data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('results', response.context)
        results = response.context['results']
        self.assertTrue(any('Test title' in r['title'] for r in results))
        self.assertTrue(any('Тег1' in r['tags'] for r in results))
        self.assertTrue(any('Компания1' in r['clients'] for r in results))
        # Проверяем, что 'stats' заполнен корректно
        self.assertEqual(response.context['stats']['keyword'], "Test")
        self.assertEqual(response.context['stats']['videos'], 1)
        self.assertEqual(response.context['stats']['downloads'], 1)
        self.assertEqual(response.context['stats']['clients'], 1)

    @patch('app.views.raw_query')
    def test_post_with_no_operations(self, mock_raw_query):
        def raw_query_side_effect(sql, params):
            # Главный агрегирующий запрос, пустой результат
            if 'GROUP BY' in sql or 'main_data' in sql or 'COUNT(' in sql:
                return []
            return []
        mock_raw_query.side_effect = raw_query_side_effect

        form_data = {
            "publication_from": "2024-01-01",
            "publication_to": "2024-12-31",
            "operation_from": "2024-01-01",
            "operation_to": "2024-12-31",
            "keyword": "Any",
        }
        response = self.client.post(self.url, form_data)
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context['stats'])
        self.assertEqual(response.context['results'], [])

    @patch('app.views.raw_query')
    def test_post_with_no_videos_found(self, mock_raw_query):
        # Главный агрегирующий запрос, пустой результат
        def raw_query_side_effect(sql, params):
            if 'GROUP BY' in sql or 'main_data' in sql or 'COUNT(' in sql:
                return []
            return []
        mock_raw_query.side_effect = raw_query_side_effect

        form_data = {
            "publication_from": "2024-01-01",
            "publication_to": "2024-12-31",
            "operation_from": "2024-01-01",
            "operation_to": "2024-12-31",
            "keyword": "X",
        }
        response = self.client.post(self.url, form_data)
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context['stats'])
        self.assertEqual(response.context['results'], [])

    @patch('app.views.raw_query')
    def test_post_with_no_titles_matching_keyword(self, mock_raw_query):
        # Главный агрегирующий запрос, пустой результат
        def raw_query_side_effect(sql, params):
            if 'GROUP BY' in sql or 'main_data' in sql or 'COUNT(' in sql:
                return []
            return []
        mock_raw_query.side_effect = raw_query_side_effect

        form_data = {
            "publication_from": "2024-01-01",
            "publication_to": "2024-12-31",
            "operation_from": "2024-01-01",
            "operation_to": "2024-12-31",
            "keyword": "Unmatched",
        }
        response = self.client.post(self.url, form_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['results'], [])

    @patch('app.views.raw_query')
    def test_post_invalid_form(self, mock_raw_query):
        form_data = {
            "publication_from": "",  # невалидно
            "publication_to": "",
            "operation_from": "2024-01-01",
            "operation_to": "2024-12-31",
            "keyword": "Test",
        }
        response = self.client.post(self.url, form_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<form')
        self.assertIn('form', response.context)
        self.assertEqual(response.context['results'], [])

    @patch('app.views.raw_query')
    def test_post_video_without_clients(self, mock_raw_query):
        def raw_query_side_effect(sql, params):
            if 'GROUP BY' in sql or 'main_data' in sql or 'COUNT(' in sql:
                return [{
                    "video_id": 42,
                    "title": "No client video",
                    "limit_type": "A",
                    "download_count": 1,
                    "agreement_ids": []
                }]
            # Без agreements и компаний
            if 'FROM content_tag_connections' in sql:
                return []
            if 'FROM content_tag_translations' in sql:
                return []
            return []

        mock_raw_query.side_effect = raw_query_side_effect

        form_data = {
            "publication_from": "2024-01-01",
            "publication_to": "2024-12-31",
            "operation_from": "2024-01-01",
            "operation_to": "2024-12-31",
            "keyword": "No",
        }
        response = self.client.post(self.url, form_data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('results', response.context)
        results = response.context['results']
        self.assertEqual(results[0]['clients'], "—")

    @patch('app.views.raw_query')
    def test_post_video_with_multiple_clients_and_tags(self, mock_raw_query):
        def raw_query_side_effect(sql, params):
            if 'GROUP BY' in sql or 'main_data' in sql or 'COUNT(' in sql:
                return [{
                    "video_id": 42,
                    "title": "Multi client video",
                    "limit_type": "A",
                    "download_count": 2,
                    "agreement_ids": [100, 101]
                }]
            if 'FROM business_agreements' in sql:
                return [
                    {"id": 100, "company_id": 200},
                    {"id": 101, "company_id": 201},
                ]
            if 'FROM business_companies' in sql:
                return [
                    {"id": 200, "name": "Компания1"},
                    {"id": 201, "name": "Компания2"},
                ]
            if 'FROM content_tag_connections' in sql:
                return [
                    {"connectable_id": 42, "tag_id": 10},
                    {"connectable_id": 42, "tag_id": 11}
                ]
            if 'FROM content_tag_translations' in sql:
                return [
                    {"content_tag_id": 10, "name": "Тег1"},
                    {"content_tag_id": 11, "name": "Тег2"},
                ]
            return []

        mock_raw_query.side_effect = raw_query_side_effect

        form_data = {
            "publication_from": "2024-01-01",
            "publication_to": "2024-12-31",
            "operation_from": "2024-01-01",
            "operation_to": "2024-12-31",
            "keyword": "Multi",
        }
        response = self.client.post(self.url, form_data)
        self.assertEqual(response.status_code, 200)
        results = response.context['results']
        self.assertIn("Компания1", results[0]['clients'])
        self.assertIn("Компания2", results[0]['clients'])
        self.assertIn("Тег1", results[0]['tags'])
        self.assertIn("Тег2", results[0]['tags'])

    @patch('app.views.raw_query')
    def test_post_video_with_clients_without_tags(self, mock_raw_query):
        def raw_query_side_effect(sql, params):
            if 'GROUP BY' in sql or 'main_data' in sql or 'COUNT(' in sql:
                return [{
                    "video_id": 42,
                    "title": "Video no tags",
                    "limit_type": "A",
                    "download_count": 1,
                    "agreement_ids": [100]
                }]
            if 'FROM business_agreements' in sql:
                return [{"id": 100, "company_id": 200}]
            if 'FROM business_companies' in sql:
                return [{"id": 200, "name": "Клиент"}]
            if 'FROM content_tag_connections' in sql:
                return []  # нет тегов
            if 'FROM content_tag_translations' in sql:
                return []
            return []

        mock_raw_query.side_effect = raw_query_side_effect

        form_data = {
            "publication_from": "2024-01-01",
            "publication_to": "2024-12-31",
            "operation_from": "2024-01-01",
            "operation_to": "2024-12-31",
            "keyword": "Video",
        }
        response = self.client.post(self.url, form_data)
        self.assertEqual(response.status_code, 200)
        results = response.context['results']
        self.assertEqual(results[0]['tags'], "—")
        self.assertIn("Клиент", results[0]['clients'])
