import pytest
from django.contrib.auth.models import User


@pytest.mark.django_db
def test_signup(client):
    response = client.post('/signup/', data={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'testpass'
    })
    assert response.status_code == 200
    assert response.data['msg'] == 'User created successfully'
    assert User.objects.filter(username='test@example.com').exists()
