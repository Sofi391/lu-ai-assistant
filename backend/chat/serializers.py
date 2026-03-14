from rest_framework import serializers


class SignupRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(help_text="User's email address (will be used as username)")
    password = serializers.CharField(min_length=8, help_text="User's password (minimum 8 characters)")
    full_name = serializers.CharField(max_length=150, required=False, help_text="User's full name (optional)")


class SignupResponseSerializer(serializers.Serializer):
    msg = serializers.CharField(help_text="Success message")


class ChatRequestSerializer(serializers.Serializer):
    question = serializers.CharField(max_length=2000, help_text="User's question or message to the AI assistant")
    session_id = serializers.UUIDField(required=False, help_text="Existing chat session ID (optional for new sessions)")
    title = serializers.CharField(max_length=100, required=False, help_text="Custom title for new session (optional)")


class IngestRequestSerializer(serializers.Serializer):
    content = serializers.CharField(help_text="Text content to be ingested into the RAG knowledge base")


class IngestResponseSerializer(serializers.Serializer):
    status = serializers.CharField(help_text="Ingestion status")


class SessionSerializer(serializers.Serializer):
    id = serializers.UUIDField(help_text="Unique session identifier")
    title = serializers.CharField(help_text="Session title")
    created_at = serializers.DateTimeField(help_text="Session creation timestamp")


class SessionListResponseSerializer(serializers.Serializer):
    sessions = SessionSerializer(many=True, help_text="List of user's chat sessions")


class UserStatusResponseSerializer(serializers.Serializer):
    username = serializers.EmailField(help_text="User's email/username")
    full_name = serializers.CharField(help_text="User's full name")
    is_admin = serializers.BooleanField(help_text="Whether user has admin privileges")
    session_count = serializers.IntegerField(help_text="Total number of chat sessions")
    message_count = serializers.IntegerField(help_text="Total number of messages sent")
    member_since = serializers.DateTimeField(help_text="Account creation date")


class ErrorResponseSerializer(serializers.Serializer):
    error = serializers.BooleanField(help_text="Error flag")
    code = serializers.CharField(help_text="Error code")
    message = serializers.CharField(help_text="Human-readable error message")


class ThrottleErrorResponseSerializer(serializers.Serializer):
    error = serializers.BooleanField(help_text="Error flag")
    code = serializers.CharField(help_text="Rate limit error code")
    message = serializers.CharField(help_text="Rate limit message with wait time")