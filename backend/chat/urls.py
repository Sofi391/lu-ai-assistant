from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView
from .views import SignupView, IngestView,ChatView,SessionListView,SessionMessages

urlpatterns = [
    path('signup/', SignupView.as_view(), name='signup'),
    path('token/', TokenObtainPairView.as_view(), name='token'),
    path('chat/', ChatView.as_view(), name='chat'),
    path('ingest/', IngestView.as_view(), name='ingest'),
    path('sessions/',SessionListView.as_view(),name='session-list'),
    path('session/<int:session_id>/messages/',SessionMessages.as_view(),name='session-messages'),
]
