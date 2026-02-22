class MockResponse:
    def ingest_text(self, content):
        return {"status": "success"}

    def get_response(self, question):
        return f"Mock response to: {question}"
