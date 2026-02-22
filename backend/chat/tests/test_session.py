import pytest
from chat.models import ChatSession


@pytest.mark.django_db
def test_list_sessions(auth_client):
    client, user = auth_client

    chat_session = ChatSession.objects.create(user=user,title="What is Pytest")
    client.force_authenticate(user=user)

    response = client.get("/sessions/")

    assert response.status_code == 200
    assert response.data[0]["title"] == "What is Pytest"
