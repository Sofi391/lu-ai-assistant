import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lu_backend.settings')
django.setup()

from chat.utils import RAGService

# Test data
test_data = "LU is a helpful and friendly chatbot created by Leul. LU's purpose is to assist users with their questions and provide accurate information from its knowledge base."

print("Testing RAGService...")
try:
    rag = RAGService()
    print("RAGService initialized successfully")
    
    # Test ingestion
    print("Ingesting test data...")
    rag.ingest_text(test_data)
    print("Data ingested successfully!")
    
    # Test query
    print("Testing query...")
    question = "Who created LU?"
    response = rag.get_response(question)
    print(f"Question: {question}")
    print(f"Response: {response}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
