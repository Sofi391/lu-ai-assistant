import pytest
from .test_chat import MockStreamingResponse


@pytest.mark.django_db
def test_chat_rate_limit(auth_client, monkeypatch):
    client, user = auth_client
    from chat import views
    monkeypatch.setattr(views, "RAGService", lambda: MockStreamingResponse())

    for _ in range(10):
        response = client.post('/chat/', {'question': 'Keep talking...'})
        assert response.status_code == 200

    response = client.post('/chat/', {'question': 'One too many!'})

    assert response.status_code == 429
    assert "detail" in response.data
    assert "Request was throttled" in response.data['detail']
