from django.contrib import admin
from .models import ChatSession,KnowledgeBase,Message

# Register your models here.
@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'title', 'created_at')
    list_filter = ('user', 'created_at')
    search_fields = ('title',)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'session__title', 'role', 'content', 'created_at')
    list_filter = ('session', 'role', 'created_at')
    search_fields = ('content',)


@admin.register(KnowledgeBase)
class KnowledgeBaseAdmin(admin.ModelAdmin):
    list_display = ('id', 'content', 'created_at')
    search_fields = ('content',)
