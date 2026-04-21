from django.urls import path
from rest_framework.routers import DefaultRouter
from . import views
from django.urls import include
router = DefaultRouter()
router.register(r'conversations', views.ConversationViewSet, basename='conversation')
router.register(r'messages', views.MessageViewSet, basename='message')

app_name = 'messaging'

urlpatterns = [
    path('', include(router.urls)),
    path('start-conversation/', views.StartConversationView.as_view(), name='start_conversation'),
    path('conversations/<int:pk>/messages/', views.ConversationMessagesView.as_view(), name='conversation_messages'),
    path('conversations/<int:pk>/typing/', views.SetTypingStatusView.as_view(), name='set_typing'),
    path('unread/', views.UnreadConversationsView.as_view(), name='unread_conversations'),
]

