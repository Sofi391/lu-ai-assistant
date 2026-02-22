import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

@pytest.fixture
def auth_client(db):
    """
    Fixture to provide an authenticated APIClient and the user object.
    The 'db' argument is required for any fixture touching the database.
    """
    user = User.objects.create_user(username='test-user', password='password123')
    client = APIClient()
    client.force_authenticate(user=user)
    return client, user
