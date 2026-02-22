import pytest
from chat.models import ChatSession,Message


class MockResponse:
    def get_response(self, question):
        return f"Mock response to: {question}"


@pytest.mark.django_db
@pytest.mark.parametrize("question, expected_status", [
    ("What is AI?", 200),
    ("Tell me a long story about RAG...", 200),
    ("", 400),  # Testing empty string if your view allows it
])
def test_chat_various_questions(auth_client, monkeypatch, question, expected_status):
    client, user = auth_client

    from chat import views
    monkeypatch.setattr(views, "RAGService", MockResponse)

    response = client.post('/chat/', {'question': question})

    assert response.status_code == expected_status
    assert response.data['response'] == f"Mock response to: {question}"
    assert "session_id" in response.data
    assert Message.objects.filter(role="user").first().content == question
