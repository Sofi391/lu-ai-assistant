from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
# from .utils import RAGService
from .mock_rag_api import MockResponse as RAGService
from .models import ChatSession, Message
import re


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
            return Response({"error": "Prompt is required"}, status=400)

        session_id = request.data.get('session_id')  # optional
        first_sentence = re.split(r'[.!?]+', question)[0].strip()[:35]
        title = request.data.get('title',first_sentence)  # optional
        if session_id:
            session = get_object_or_404(ChatSession, id=session_id, user=request.user)
        else:
            session = ChatSession.objects.create(
                user=request.user,
                title=title
            )

        MEMORY_WINDOW = 10
        Message.objects.create(session=session, role="user", content=question)
        context = Message.objects.filter(session=session).order_by('-created_at')[:MEMORY_WINDOW]
        context = reversed(context)
        context_messages = "\n".join([f"{msg.role}:{msg.content}" for msg in context])
        rag = RAGService()
        answer = rag.get_response(context_messages)

        Message.objects.create(session=session, role="assistant", content=answer)

        return Response({
            "response": answer,
            "session_id": session.id
        })


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
