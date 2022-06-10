import pytest
from rest_framework.test import APIClient


@pytest.fixture
def user(django_user_model):
    return django_user_model.objects.create_user(
        username='TestUser01',
        email='test@test.testtest',
        password='12344321',
    )


@pytest.fixture
def user_client(user, client):
    """ Авторизованный пользователь + клиент """
    client.force_login(user)
    return user, client


@pytest.fixture
def api_client():
    return APIClient()
