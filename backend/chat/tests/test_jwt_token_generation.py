import pytest


@pytest.mark.django_db
def test_obtain_jwt_token(client,test_user):
    response = client.post('/token/', {'username': test_user.username, 'password': 'password123'})

    assert response.status_code == 200
    assert 'access' in response.data
    assert 'refresh' in response.data
