from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Task


class TaskAPITests(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='rahma', password='test1234')
        self.user2 = User.objects.create_user(username='sara', password='test1234')

    def auth(self, user):
        access_token = RefreshToken.for_user(user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

    def test_register(self):
        response = self.client.post(
            '/api/register/',
            {'username': 'newuser', 'password': 'test1234'},
            format='json',
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_register_ignores_authorization_header(self):
        self.client.credentials(HTTP_AUTHORIZATION='Basic invalid')
        response = self.client.post(
            '/api/register/',
            {'username': 'anotheruser', 'password': 'test1234'},
            format='json',
        )
        self.assertEqual(response.status_code, 201)

    def test_register_schema_is_public(self):
        response = self.client.get('/api/schema/')
        self.assertEqual(response.status_code, 200)
        operation = response.data['paths']['/api/register/']['post']
        self.assertNotIn('security', operation)

    def test_schema_uses_jwt_authentication(self):
        response = self.client.get('/api/schema/')
        self.assertEqual(response.status_code, 200)
        schemes = response.data['components']['securitySchemes']
        self.assertIn('jwtAuth', schemes)
        self.assertNotIn('basicAuth', schemes)

    def test_tasks_require_authentication(self):
        response = self.client.get('/api/tasks/')
        self.assertEqual(response.status_code, 401)
        self.assertTrue(response['WWW-Authenticate'].startswith('Bearer'))

    def test_tasks_accept_jwt_authentication(self):
        self.auth(self.user1)
        response = self.client.get('/api/tasks/')
        self.assertEqual(response.status_code, 200)

    def test_api_root_is_public(self):
        response = self.client.get('/api/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('tasks', response.data)

    def test_create_task_sets_owner(self):
        self.auth(self.user1)
        response = self.client.post('/api/tasks/', {'title': 'Study Django'}, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['owner'], 'rahma')

    def test_user_sees_only_own_tasks(self):
        Task.objects.create(owner=self.user1, title='Rahma task')
        Task.objects.create(owner=self.user2, title='Sara task')
        self.auth(self.user1)
        response = self.client.get('/api/tasks/')
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['title'], 'Rahma task')

    def test_filter_by_is_done(self):
        Task.objects.create(owner=self.user1, title='Done task', is_done=True)
        Task.objects.create(owner=self.user1, title='Open task', is_done=False)
        self.auth(self.user1)
        response = self.client.get('/api/tasks/?is_done=true')
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['title'], 'Done task')
