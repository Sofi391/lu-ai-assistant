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


@pytest.fixture
def api_client(db):
    """Fixture to provide an unauthenticated APIClient."""
    return APIClient()


@pytest.fixture
def test_user(db):
    """Fixture to create a test user."""
    user = User.objects.create_user(username='test-user', password='password123')
    return user

@pytest.fixture
def admin_user(db):
    """Fixture to create an admin user."""
    user = User.objects.create_user(username='admin', password='adminpass', is_staff=True)
    return user

