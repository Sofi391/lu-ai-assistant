from rest_framework.exceptions import Throttled
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.http import StreamingHttpResponse
from drf_spectacular.utils import extend_schema, OpenApiResponse
from .services.rag_service import RAGService
# from .mock_rag_api import MockResponse as RAGService
from .models import ChatSession, Message
from .serializers import (
    SignupRequestSerializer, SignupResponseSerializer,
    ChatRequestSerializer, IngestRequestSerializer, IngestResponseSerializer,
    SessionListResponseSerializer, ErrorResponseSerializer, ThrottleErrorResponseSerializer
)
import re
import logging
import time


logger = logging.getLogger("chat")

MAX_INPUT_LENGTH = 2000
MEMORY_WINDOW = 10

def mask_email(email):
    """Mask email for privacy in logs (GDPR compliance)"""
    if not email or '@' not in email:
        return "***"
    local, domain = email.split('@', 1)
    if len(local) <= 2:
        return f"{local[0]}***@{domain}"
    return f"{local[0]}***{local[-1]}@{domain}"


class SignupView(APIView):
    permission_classes = [AllowAny]
    
    @extend_schema(
        summary="Register a new user account",
        description="Creates a new user account with email, password, and optional full name.",
        request=SignupRequestSerializer,
        responses={
            200: SignupResponseSerializer,
            400: ErrorResponseSerializer,
            500: ErrorResponseSerializer,
        },
    )
    def post(self, request):
        start_time = time.time()
        email = request.data.get('email')
        masked_email = mask_email(email)
        logger.info(f"Signup request started for email: {masked_email}")
        
        password = request.data.get('password')
        full_name = request.data.get('full_name', '')
        
        if User.objects.filter(username=email).exists():
            logger.warning(f"Signup failed: User already exists - {masked_email}")
            return Response({"error": "User already exists"}, status=400)
        
        try:
            user = User.objects.create_user(username=email, email=email, password=password, first_name=full_name)
            elapsed = time.time() - start_time
            logger.info(f"Signup successful for {masked_email} - took {elapsed:.2f}s")
            return Response({"msg": "User created successfully"})
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Signup error for {masked_email}: {str(e)} - took {elapsed:.2f}s")
            return Response({"error": "Failed to create user"}, status=500)


class ChatView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_scope = "chat"
    
    def throttled(self, request, wait):
        logger.warning(f"Chat request throttled - User: {request.user.username}, Wait: {wait}s")
        raise Throttled(wait)

    @extend_schema(
        summary="Send a message to the AI assistant",
        description="Processes a user question via RAG and returns a streaming text response with conversation context.",
        request=ChatRequestSerializer,
        responses={
            200: OpenApiResponse(
                description="Streaming text response from AI assistant",
                response=str
            ),
            400: ErrorResponseSerializer,
            404: ErrorResponseSerializer,
            429: ThrottleErrorResponseSerializer,
            500: ErrorResponseSerializer,
        },
    )
    def post(self, request):
        question = request.data.get('question','').strip()
        logger.info(f"Chat request started - User: {request.user.username}, Question length: {len(question)}")
        
        if not question:
            logger.warning(f"Chat request failed: Empty question - User: {request.user.username}")
            return Response({
                  "error": True,
                  "code": "INVALID_INPUT",
                  "message": "Prompt is required"
                }, status=400)
        if len(question) > MAX_INPUT_LENGTH:
            logger.warning(f"Chat request failed: Input too long ({len(question)} chars) - User: {request.user.username}")
            return Response({
                  "error": True,
                  "code": "INPUT_TOO_LONG",
                  "message": f"Input exceeds maximum length of {MAX_INPUT_LENGTH} characters"
                }, status=400)

        session_id = request.data.get('session_id')
        first_sentence = re.split(r'[.!?]+', question)[0].strip()[:35]
        title = request.data.get('title',first_sentence)
        try:
            if session_id:
                session = ChatSession.objects.get(id=session_id, user=request.user)
                logger.info(f"Using existing session {session_id} - User: {request.user.username}")
            else:
                session = ChatSession.objects.create(
                    user=request.user,
                    title=title
                )
                logger.info(f"Created new session {session.id} - User: {request.user.username}")
        except ChatSession.DoesNotExist:
            logger.error(f"Session not found: {session_id} - User: {request.user.username}")
            return Response({
                "error": True,
                "code": "SESSION_NOT_FOUND",
                "message": "Chat session not found."
            }, status=404)
        except Exception as e:
            logger.error(f"Session error: {str(e)} - User: {request.user.username}")
            return Response({
                "error": True,
                "code": "SESSION_ERROR",
                "message": "Failed to create or retrieve session."
            }, status=500)
        
        Message.objects.create(session=session, role="user", content=question)
        last_question = question
        context = Message.objects.filter(session=session).order_by('-created_at')[1:MEMORY_WINDOW+1]
        context = reversed(context)
        messaging_history = "\n".join([f"{msg.role.capitalize()}:{msg.content}" for msg in context])
        
        try:
            rag = RAGService()
            logger.info(f"RAG service initialized - Session: {session.id}")
        except Exception as e:
            logger.error(f"RAG service initialization failed: {str(e)} - Session: {session.id}")
            return Response({
                "error": True,
                "code": "RAG_SERVICE_ERROR",
                "message": "AI service failed to initialize."
            }, status=500)

        def stream_wrapper():
            full_answer = ""
            chunks_sent = 0
            stream_start = time.time()
            try:
                logger.info(f"Starting stream response - Session: {session.id}")
                for chunk in rag.get_response_stream(question=last_question, history=messaging_history):
                    full_answer += chunk
                    chunks_sent +=1
                    yield chunk

                if full_answer:
                    Message.objects.create(session=session, role="assistant", content=full_answer)
                    elapsed = time.time() - stream_start
                    logger.info(f"Stream completed - Session: {session.id}, Chunks: {chunks_sent}, AI Time: {elapsed:.2f}s")

            except Exception as e:
                logger.error(f"Stream error: {str(e)} - Session: {session.id}, Chunks sent: {chunks_sent}")
                if chunks_sent == 0:
                    try:
                        logger.info(f"Attempting fallback response - Session: {session.id}")
                        fallback_answer = rag.get_response(question=last_question, history=messaging_history)
                        Message.objects.create(session=session, role="assistant", content=fallback_answer)
                        elapsed = time.time() - stream_start
                        logger.info(f"Fallback response successful - Session: {session.id}, AI Time: {elapsed:.2f}s")
                        yield fallback_answer
                    except Exception as fallback_error:
                        elapsed = time.time() - stream_start
                        logger.error(f"Fallback failed: {str(fallback_error)} - Session: {session.id}, AI Time: {elapsed:.2f}s")
                        yield "\n\nI'm sorry, I encountered a connection error. Please try again."
                else:
                    logger.warning(f"Stream interrupted after {chunks_sent} chunks - Session: {session.id}")
        
        logger.info(f"Returning streaming response with Session ID: {session.id} in header")
        response = StreamingHttpResponse(stream_wrapper(), content_type='text/plain')
        response['X-Session-ID'] = session.id
        response['Access-Control-Expose-Headers'] = 'X-Session-ID'

        return response


class IngestView(APIView):
    permission_classes = [IsAuthenticated,IsAdminUser]
    throttle_scope = "ingest"
    
    def throttled(self, request, wait):
        logger.warning(f"Ingest request throttled - User: {request.user.username}, Wait: {wait}s")
        raise Throttled(wait)

    @extend_schema(
        summary="Ingest content into RAG knowledge base",
        description="Adds text content to the RAG system's knowledge base for future query retrieval.",
        request=IngestRequestSerializer,
        responses={
            200: IngestResponseSerializer,
            400: ErrorResponseSerializer,
            429: ThrottleErrorResponseSerializer,
            500: ErrorResponseSerializer,
        },
    )
    def post(self, request):
        start_time = time.time()
        content = request.data.get('content')
        logger.info(f"Ingest request started - User: {request.user.username}, Content length: {len(content) if content else 0}")
        
        if not content:
            logger.warning(f"Ingest failed: Empty content - User: {request.user.username}")
            return Response({
                "error": True,
                "code": "INVALID_INPUT",
                "message": "Content is required"
            }, status=400)
        
        try:
            rag = RAGService()
            rag.ingest_text(content)
            elapsed = time.time() - start_time
            logger.info(f"Ingest successful - User: {request.user.username}, Time: {elapsed:.2f}s")
            return Response({"status": "success"})
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Ingest error: {str(e)} - User: {request.user.username}, Time: {elapsed:.2f}s")
            return Response({
                "error": True,
                "code": "INGEST_ERROR",
                "message": "Failed to ingest content"
            }, status=500)


class SessionListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get user's chat sessions",
        description="Retrieves a list of all chat sessions for the authenticated user, ordered by creation date.",
        responses={
            200: SessionListResponseSerializer,
            500: ErrorResponseSerializer,
        },
    )
    def get(self, request):
        start_time = time.time()
        logger.info(f"Session list request - User: {request.user.username}")
        
        try:
            sessions = ChatSession.objects.filter(user=request.user).order_by('-created_at')
            data = [{
                "id": session.id,
                "title": session.title,
                "created_at": session.created_at.strftime('%Y-%m-%d %H:%M:%S')
                }
                for session in sessions]
            
            elapsed = time.time() - start_time
            logger.info(f"Session list retrieved - User: {request.user.username}, Count: {len(data)}, Time: {elapsed:.2f}s")
            return Response(data)
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Session list error: {str(e)} - User: {request.user.username}, Time: {elapsed:.2f}s")
            return Response({"error": "Failed to retrieve sessions"}, status=500)


class SessionMessages(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, session_id):
        start_time = time.time()
        logger.info(f"Session messages request - User: {request.user.username}, Session: {session_id}")
        
        try:
            session = get_object_or_404(ChatSession.objects.prefetch_related('messages'), id=session_id, user=request.user)

            data = [{
                "role": message.role,
                "content": message.content,
                "timestamp": message.created_at.strftime('%Y-%m-%d %H:%M:%S')
                }
                for message in session.messages.all()]
            
            elapsed = time.time() - start_time
            logger.info(f"Session messages retrieved - Session: {session_id}, Count: {len(data)}, Time: {elapsed:.2f}s")
            return Response(data)
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Session messages error: {str(e)} - Session: {session_id}, Time: {elapsed:.2f}s")
            return Response({"error": "Failed to retrieve messages"}, status=500)
