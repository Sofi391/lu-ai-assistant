import pytest
from chat.models import Message,ChatSession

class MockStreamingResponse:
    def get_response_stream(self, question, history=None):
        yield f"Mock response to: {question}"

    def get_response(self, question, history=None):
        return f"Mock response to: {question}"

@pytest.mark.django_db
@pytest.mark.parametrize("question, expected_status", [
    ("What is AI?", 200),
    ("Tell me a long story...", 200),
    ("", 400)
])
def test_chat_streaming(auth_client, monkeypatch, question, expected_status):
    client, user = auth_client
    from chat import views
    monkeypatch.setattr(views, "RAGService", lambda: MockStreamingResponse())

    response = client.post('/chat/', {'question': question})
    assert response.status_code == expected_status

    if expected_status == 200:
        full_response = b"".join(response.streaming_content).decode()
        assert full_response == f"Mock response to: {question}"
    else:
        assert response.status_code == 400
