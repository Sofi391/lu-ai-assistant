import pytest


@pytest.mark.django_db
def test_admin_only_permission(api_client,test_user,admin_user):
    api_client.force_authenticate(test_user)
    response = api_client.post("/ingest/")
    assert response.status_code == 403

    api_client.force_authenticate(admin_user)
    response = api_client.post("/ingest/",{"content": "dummy"})
    assert response.status_code == 200


@pytest.mark.django_db
def test_ingest_ratelimit(api_client,admin_user):
    api_client.force_authenticate(admin_user)
    for _ in range(5):
        response = api_client.post("/ingest/", {"content": "dummy"})
        assert response.status_code == 200

    response = api_client.post("/ingest/", {"content": "no dummies no more!"})
    assert response.status_code == 429


@pytest.mark.django_db
def test_ingest_unauthenticated(client):
    response = client.post("/ingest/")
    assert response.status_code == 401


