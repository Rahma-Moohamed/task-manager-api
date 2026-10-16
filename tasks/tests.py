from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework.authtoken.models import Token

from .models import Task


class TaskAPITests(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='rahma', password='test1234')
        self.user2 = User.objects.create_user(username='sara', password='test1234')
        self.token1 = Token.objects.create(user=self.user1)
        self.token2 = Token.objects.create(user=self.user2)

    def auth(self, token):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

    def test_register(self):
        response = self.client.post(
            '/api/register/',
            {'username': 'newuser', 'password': 'test1234'},
            format='json',
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_login_returns_token(self):
        response = self.client.post(
            '/api/login/',
            {'username': 'rahma', 'password': 'test1234'},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('token', response.data)

    def test_tasks_require_authentication(self):
        response = self.client.get('/api/tasks/')
        self.assertEqual(response.status_code, 401)

    def test_create_task_sets_owner(self):
        self.auth(self.token1)
        response = self.client.post('/api/tasks/', {'title': 'Study Django'}, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['owner'], 'rahma')

    def test_user_sees_only_own_tasks(self):
        Task.objects.create(owner=self.user1, title='Rahma task')
        Task.objects.create(owner=self.user2, title='Sara task')
        self.auth(self.token1)
        response = self.client.get('/api/tasks/')
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['title'], 'Rahma task')

    def test_filter_by_is_done(self):
        Task.objects.create(owner=self.user1, title='Done task', is_done=True)
        Task.objects.create(owner=self.user1, title='Open task', is_done=False)
        self.auth(self.token1)
        response = self.client.get('/api/tasks/?is_done=true')
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['title'], 'Done task')
