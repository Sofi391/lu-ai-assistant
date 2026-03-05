from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.http import StreamingHttpResponse
from .services.rag_service import RAGService
# from .mock_rag_api import MockResponse as RAGService
from .models import ChatSession, Message
import re


MAX_INPUT_LENGTH = 2000
MEMORY_WINDOW = 10

class SignupView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        full_name = request.data.get('full_name', '')
        
        if User.objects.filter(username=email).exists():
            return Response({"error": "User already exists"}, status=400)
            
        user = User.objects.create_user(username=email, email=email, password=password, first_name=full_name)
        return Response({"msg": "User created successfully"})


class ChatView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        question = request.data.get('question','').strip()
        if not question:
            return Response({
                  "error": True,
                  "code": "INVALID_INPUT",
                  "message": "Prompt is required"
                }, status=400)
        if len(question) > MAX_INPUT_LENGTH:
            return Response({
                  "error": True,
                  "code": "INPUT_TOO_LONG",
                  "message": f"Input exceeds maximum length of {MAX_INPUT_LENGTH} characters"
                }, status=400)

        session_id = request.data.get('session_id')  # optional
        first_sentence = re.split(r'[.!?]+', question)[0].strip()[:35]
        title = request.data.get('title',first_sentence)  # optional
        try:
            if session_id:
                session = ChatSession.objects.get(id=session_id, user=request.user)
            else:
                session = ChatSession.objects.create(
                    user=request.user,
                    title=title
                )
        except ChatSession.DoesNotExist:
            return Response({
                "error": True,
                "code": "SESSION_NOT_FOUND",
                "message": "Chat session not found."
            }, status=400)
        Message.objects.create(session=session, role="user", content=question)
        last_question = question
        context = Message.objects.filter(session=session).order_by('-created_at')[1:MEMORY_WINDOW+1]
        context = reversed(context)
        messaging_history = "\n".join([f"{msg.role.capitalize()}:{msg.content}" for msg in context])
        try:
            rag = RAGService()
        except Exception as e:
            return Response({
                "error": True,
                "code": "RAG_SERVICE_ERROR",
                "message": "AI service failed to initialize."
            }, status=500)

        def stream_wrapper():
            full_answer = ""
            chunks_sent = 0
            try:
                for chunk in rag.get_response_stream(question=last_question, history=messaging_history):
                    full_answer += chunk
                    chunks_sent +=1
                    yield chunk

                if full_answer:
                    Message.objects.create(session=session, role="assistant", content=full_answer)

            except Exception as e:
                if chunks_sent == 0:
                    try:
                        fallback_answer = rag.get_response(question=last_question, history=messaging_history)
                        Message.objects.create(session=session, role="assistant", content=fallback_answer)
                        yield fallback_answer
                    except:
                        yield "\n\nI'm sorry, I encountered a connection error. Please try again."
                else:
                    print(f"Stream interrupted: {e}")
        response = StreamingHttpResponse(stream_wrapper(), content_type='text/plain')
        response['X-Session-ID'] = session.id
        response['Access-Control-Expose-Headers'] = 'X-Session-ID'

        return response


class IngestView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        content = request.data.get('content')
        rag = RAGService()
        rag.ingest_text(content)
        return Response({"status": "success"})


class SessionListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        sessions = ChatSession.objects.filter(user=request.user).order_by('-created_at')
        data = [{
            "id": session.id,
            "title": session.title,
            "created_at": session.created_at.strftime('%Y-%m-%d %H:%M:%S')
            }
            for session in sessions]

        return Response(data)


class SessionMessages(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, session_id):
        session = get_object_or_404(ChatSession.objects.prefetch_related('messages'), id=session_id, user=request.user)

        data = [{
            "role": message.role,
            "content": message.content,
            "timestamp": message.created_at.strftime('%Y-%m-%d %H:%M:%S')
            }
            for message in session.messages.all()]

        return Response(data)
