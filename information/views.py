from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse

from users.decorators import teacher_required, parent_required
from .models import Event, Announcement, ChatRoom, ChatMessage, Notification, BotMessage


# ========================================
# Events
# ========================================

@login_required
def event_list(request):
    """List all upcoming events"""
    from datetime import date
    
    events = Event.objects.filter(
        is_active=True,
        start_date__gte=date.today()
    ).order_by('start_date')
    
    context = {
        'events': events,
    }
    return render(request, 'information/event_list.html', context)


@login_required
def event_detail(request, event_id):
    """View event details"""
    event = get_object_or_404(Event, id=event_id)
    
    context = {
        'event': event,
    }
    return render(request, 'information/event_detail.html', context)


@login_required
@teacher_required
def create_event(request):
    """Create new event (teachers only)"""
    teacher = request.user.teacher_profile
    
    if request.method == 'POST':
        # Handle event creation
        messages.success(request, 'Event created successfully!')
        return redirect('information:event_list')
    
    context = {
        'teacher': teacher,
    }
    return render(request, 'information/create_event.html', context)


@login_required
@teacher_required
def edit_event(request, event_id):
    """Edit event"""
    teacher = request.user.teacher_profile
    event = get_object_or_404(Event, id=event_id, created_by=teacher)
    
    if request.method == 'POST':
        # Handle event editing
        messages.success(request, 'Event updated successfully!')
        return redirect('information:event_detail', event_id=event_id)
    
    context = {
        'event': event,
        'teacher': teacher,
    }
    return render(request, 'information/edit_event.html', context)


@login_required
@teacher_required
def delete_event(request, event_id):
    """Delete event"""
    teacher = request.user.teacher_profile
    event = get_object_or_404(Event, id=event_id, created_by=teacher)
    
    if request.method == 'POST':
        event.delete()
        messages.success(request, 'Event deleted successfully!')
        return redirect('information:event_list')
    
    return redirect('information:event_detail', event_id=event_id)


# ========================================
# Announcements
# ========================================

@login_required
def announcement_list(request):
    """List all announcements"""
    announcements = Announcement.objects.filter(
        is_published=True
    ).order_by('-created_at')
    
    # Filter by role
    if request.user.is_parent():
        announcements = announcements.filter(
            target_audience__in=['all', 'parents']
        )
    elif request.user.is_teacher():
        announcements = announcements.filter(
            target_audience__in=['all', 'teachers']
        )
    
    context = {
        'announcements': announcements,
    }
    return render(request, 'information/announcement_list.html', context)


@login_required
def announcement_detail(request, announcement_id):
    """View announcement details"""
    announcement = get_object_or_404(Announcement, id=announcement_id, is_published=True)
    
    # Mark as read
    from .models import AnnouncementRead
    AnnouncementRead.objects.get_or_create(
        announcement=announcement,
        user=request.user
    )
    
    # Increment view count
    announcement.views_count += 1
    announcement.save()
    
    context = {
        'announcement': announcement,
    }
    return render(request, 'information/announcement_detail.html', context)


@login_required
@teacher_required
def create_announcement(request):
    """Create new announcement (teachers only)"""
    teacher = request.user.teacher_profile
    
    if request.method == 'POST':
        # Handle announcement creation
        messages.success(request, 'Announcement created successfully!')
        return redirect('information:announcement_list')
    
    context = {
        'teacher': teacher,
    }
    return render(request, 'information/create_announcement.html', context)


@login_required
@teacher_required
def edit_announcement(request, announcement_id):
    """Edit announcement"""
    teacher = request.user.teacher_profile
    announcement = get_object_or_404(Announcement, id=announcement_id, posted_by=teacher)
    
    if request.method == 'POST':
        # Handle announcement editing
        messages.success(request, 'Announcement updated successfully!')
        return redirect('information:announcement_detail', announcement_id=announcement_id)
    
    context = {
        'announcement': announcement,
        'teacher': teacher,
    }
    return render(request, 'information/edit_announcement.html', context)


@login_required
@teacher_required
def delete_announcement(request, announcement_id):
    """Delete announcement"""
    teacher = request.user.teacher_profile
    announcement = get_object_or_404(Announcement, id=announcement_id, posted_by=teacher)
    
    if request.method == 'POST':
        announcement.delete()
        messages.success(request, 'Announcement deleted successfully!')
        return redirect('information:announcement_list')
    
    return redirect('information:announcement_detail', announcement_id=announcement_id)


# ========================================
# Chat System
# ========================================

@login_required
def chat_list(request):
    """List all chat rooms for user"""
    if request.user.is_parent():
        parent = request.user.parent_profile
        chat_rooms = ChatRoom.objects.filter(
            parent=parent,
            is_active=True
        ).select_related('teacher__user').order_by('-last_message_at')
    elif request.user.is_teacher():
        teacher = request.user.teacher_profile
        chat_rooms = ChatRoom.objects.filter(
            teacher=teacher,
            is_active=True
        ).select_related('parent__user').order_by('-last_message_at')
    else:
        chat_rooms = []
    
    context = {
        'chat_rooms': chat_rooms,
    }
    return render(request, 'information/chat_list.html', context)


@login_required
def chat_room(request, room_id):
    """View chat room messages"""
    if request.user.is_parent():
        parent = request.user.parent_profile
        room = get_object_or_404(ChatRoom, id=room_id, parent=parent)
    elif request.user.is_teacher():
        teacher = request.user.teacher_profile
        room = get_object_or_404(ChatRoom, id=room_id, teacher=teacher)
    else:
        return redirect('information:chat_list')
    
    # Get messages
    messages_list = room.messages.all().order_by('created_at')
    
    # Mark messages as read
    unread_messages = messages_list.filter(is_read=False).exclude(sender=request.user)
    for msg in unread_messages:
        msg.mark_as_read()
    
    context = {
        'room': room,
        'messages': messages_list,
    }
    return render(request, 'information/chat_room.html', context)


@login_required
@parent_required
def start_chat(request, teacher_id):
    """Start a new chat with teacher"""
    parent = request.user.parent_profile
    from users.models import Teacher
    
    teacher = get_object_or_404(Teacher, id=teacher_id)
    
    # Get or create chat room
    room, created = ChatRoom.objects.get_or_create(
        parent=parent,
        teacher=teacher
    )
    
    if created:
        messages.success(request, 'Chat started successfully!')
    
    return redirect('information:chat_room', room_id=room.id)


@login_required
def send_message(request, room_id):
    """Send a message in chat room (AJAX)"""
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        
        if not content:
            return JsonResponse({'error': 'Message cannot be empty'}, status=400)
        
        # Verify access to room
        if request.user.is_parent():
            parent = request.user.parent_profile
            room = get_object_or_404(ChatRoom, id=room_id, parent=parent)
        elif request.user.is_teacher():
            teacher = request.user.teacher_profile
            room = get_object_or_404(ChatRoom, id=room_id, teacher=teacher)
        else:
            return JsonResponse({'error': 'Unauthorized'}, status=403)
        
        # Create message
        message = ChatMessage.objects.create(
            chat_room=room,
            sender=request.user,
            content=content,
            message_type='text'
        )
        
        # Update room's last message time
        from django.utils import timezone
        room.last_message_at = timezone.now()
        room.save()
        
        return JsonResponse({
            'success': True,
            'message_id': message.id,
            'content': message.content,
            'created_at': message.created_at.isoformat()
        })
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


@login_required
def mark_messages_read(request, room_id):
    """Mark all messages as read (AJAX)"""
    if request.user.is_parent():
        parent = request.user.parent_profile
        room = get_object_or_404(ChatRoom, id=room_id, parent=parent)
    elif request.user.is_teacher():
        teacher = request.user.teacher_profile
        room = get_object_or_404(ChatRoom, id=room_id, teacher=teacher)
    else:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    # Mark messages as read
    unread = room.messages.filter(is_read=False).exclude(sender=request.user)
    count = unread.count()
    
    for msg in unread:
        msg.mark_as_read()
    
    return JsonResponse({'success': True, 'count': count})


# ========================================
# Notifications
# ========================================

@login_required
def notification_list(request):
    """List all notifications for user"""
    notifications = Notification.objects.filter(
        recipient=request.user
    ).order_by('-created_at')
    
    context = {
        'notifications': notifications,
    }
    return render(request, 'information/notification_list.html', context)


@login_required
def mark_notification_read(request, notification_id):
    """Mark notification as read"""
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    notification.mark_as_read()
    
    if request.is_ajax():
        return JsonResponse({'success': True})
    
    return redirect('information:notification_list')


@login_required
def mark_all_notifications_read(request):
    """Mark all notifications as read"""
    Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).update(is_read=True)
    
    messages.success(request, 'All notifications marked as read!')
    return redirect('information:notification_list')


# ========================================
# Chatbot
# ========================================

@login_required
def chatbot(request):
    """Chatbot interface"""
    context = {}
    return render(request, 'information/chatbot.html', context)


@login_required
def chatbot_query(request):
    """Process chatbot query (AJAX)"""
    if request.method == 'POST':
        query = request.POST.get('query', '').strip().lower()
        
        if not query:
            return JsonResponse({'error': 'Query cannot be empty'}, status=400)
        
        # Search for matching bot message
        bot_messages = BotMessage.objects.filter(is_active=True).order_by('-priority')
        
        response = None
        for bot_msg in bot_messages:
            keywords = bot_msg.get_keywords_list()
            if any(keyword in query for keyword in keywords):
                response = bot_msg.response_text
                
                # Increment usage count
                bot_msg.usage_count += 1
                bot_msg.save()
                break
        
        if not response:
            response = "I'm sorry, I don't understand. Please try rephrasing your question or contact support."
        
        return JsonResponse({
            'success': True,
            'response': response
        })
    
    return JsonResponse({'error': 'Invalid request'}, status=400)