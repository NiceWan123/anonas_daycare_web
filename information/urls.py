from django.urls import path
from . import views

app_name = 'information'

urlpatterns = [
    # ========================================
    # Events
    # ========================================
    path('events/', views.event_list, name='event_list'),
    path('event/<int:event_id>/', views.event_detail, name='event_detail'),
    path('event/create/', views.create_event, name='create_event'),
    path('event/<int:event_id>/edit/', views.edit_event, name='edit_event'),
    path('event/<int:event_id>/delete/', views.delete_event, name='delete_event'),
    
    # ========================================
    # Announcements
    # ========================================
    path('announcements/', views.announcement_list, name='announcement_list'),
    path('announcement/<int:announcement_id>/', views.announcement_detail, name='announcement_detail'),
    path('announcement/create/', views.create_announcement, name='create_announcement'),
    path('announcement/<int:announcement_id>/edit/', views.edit_announcement, name='edit_announcement'),
    path('announcement/<int:announcement_id>/delete/', views.delete_announcement, name='delete_announcement'),
    
    # ========================================
    # Chat System
    # ========================================
    path('chat/', views.chat_list, name='chat_list'),
    path('chat/<int:room_id>/', views.chat_room, name='chat_room'),
    path('chat/start/<int:teacher_id>/', views.start_chat, name='start_chat'),
    path('chat/<int:room_id>/send/', views.send_message, name='send_message'),
    path('chat/<int:room_id>/mark-read/', views.mark_messages_read, name='mark_messages_read'),
    
    # ========================================
    # Notifications
    # ========================================
    path('notifications/', views.notification_list, name='notification_list'),
    path('notification/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    
    # ========================================
    # Chatbot
    # ========================================
    path('chatbot/', views.chatbot, name='chatbot'),
    path('chatbot/query/', views.chatbot_query, name='chatbot_query'),
]