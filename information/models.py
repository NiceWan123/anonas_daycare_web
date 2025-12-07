from django.db import models
from users.models import User, Teacher, Parent


class Event(models.Model):
    """School events - scheduled or one-time"""
    EVENT_TYPE_CHOICES = [
        ('one_time', 'One-Time Event'),
        ('recurring', 'Recurring Event'),
        ('scheduled', 'Scheduled Event'),
    ]
    
    RECURRENCE_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    
    # Event Type
    event_type = models.CharField(max_length=20, choices=EVENT_TYPE_CHOICES, default='one_time')
    
    # Date & Time
    start_date = models.DateField()
    end_date = models.DateField()
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    
    # For recurring events
    recurrence_pattern = models.CharField(
        max_length=20, 
        choices=RECURRENCE_CHOICES, 
        null=True, 
        blank=True
    )
    recurrence_end_date = models.DateField(null=True, blank=True)
    
    # Location
    location = models.CharField(max_length=200)
    venue_details = models.TextField(blank=True)
    
    # Visibility
    is_public = models.BooleanField(default=True, help_text="Visible to all parents")
    target_grades = models.CharField(
        max_length=200, 
        blank=True, 
        help_text="Comma-separated grade levels if specific"
    )
    
    # Organizer
    created_by = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True)
    
    # Attachments
    image = models.ImageField(upload_to='events/', null=True, blank=True)
    attachment = models.FileField(upload_to='event_files/', null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_cancelled = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.title} - {self.start_date}"
    
    def is_upcoming(self):
        from datetime import date
        return self.start_date >= date.today() and not self.is_cancelled
    
    class Meta:
        ordering = ['-start_date', '-created_at']
        verbose_name = "Event"
        verbose_name_plural = "Events"


class Announcement(models.Model):
    """General announcements for parents and teachers"""
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    CATEGORY_CHOICES = [
        ('academic', 'Academic'),
        ('administrative', 'Administrative'),
        ('health', 'Health & Safety'),
        ('event', 'Event'),
        ('general', 'General'),
    ]
    
    title = models.CharField(max_length=200)
    content = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='general')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    
    # Targeting
    target_audience = models.CharField(
        max_length=200,
        default='all',
        help_text="all, parents, teachers, or specific grades"
    )
    
    # Author
    posted_by = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True)
    
    # Attachments
    image = models.ImageField(upload_to='announcements/', null=True, blank=True)
    attachment = models.FileField(upload_to='announcement_files/', null=True, blank=True)
    
    # Visibility
    is_published = models.BooleanField(default=True)
    publish_date = models.DateTimeField(auto_now_add=True)
    expiry_date = models.DateTimeField(null=True, blank=True)
    
    # Engagement
    views_count = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.title} - {self.priority}"
    
    def is_expired(self):
        from django.utils import timezone
        if self.expiry_date:
            return timezone.now() > self.expiry_date
        return False
    
    class Meta:
        ordering = ['-priority', '-created_at']
        verbose_name = "Announcement"
        verbose_name_plural = "Announcements"


class AnnouncementRead(models.Model):
    """Track which parents have read announcements"""
    announcement = models.ForeignKey(Announcement, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    read_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['announcement', 'user']


class BotMessage(models.Model):
    """Predetermined chatbot responses"""
    CATEGORY_CHOICES = [
        ('greeting', 'Greeting'),
        ('faq', 'FAQ'),
        ('enrollment', 'Enrollment'),
        ('grades', 'Grades'),
        ('attendance', 'Attendance'),
        ('payment', 'Payment'),
        ('schedule', 'Schedule'),
        ('contact', 'Contact Info'),
        ('general', 'General'),
    ]
    
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    
    # Trigger keywords (comma-separated)
    keywords = models.TextField(help_text="Comma-separated keywords that trigger this response")
    
    # Response
    response_text = models.TextField()
    
    # Optional structured response
    has_buttons = models.BooleanField(default=False)
    button_options = models.JSONField(
        null=True, 
        blank=True,
        help_text="JSON array of button options"
    )
    
    # Priority (higher number = higher priority)
    priority = models.PositiveIntegerField(default=0)
    
    # Usage tracking
    usage_count = models.PositiveIntegerField(default=0)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.category} - {self.keywords[:50]}"
    
    def get_keywords_list(self):
        return [k.strip().lower() for k in self.keywords.split(',')]
    
    class Meta:
        ordering = ['-priority', 'category']
        verbose_name = "Bot Message"
        verbose_name_plural = "Bot Messages"


class ChatRoom(models.Model):
    """Real-time chat between parent and teacher"""
    parent = models.ForeignKey(Parent, on_delete=models.CASCADE, related_name='chat_rooms')
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='chat_rooms')
    
    # Room info
    subject = models.CharField(max_length=200, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_archived = models.BooleanField(default=False)
    
    # Last activity
    last_message_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Chat: {self.parent.user.get_full_name()} ↔ {self.teacher.user.get_full_name()}"
    
    def get_unread_count(self, user):
        """Get unread message count for a specific user"""
        return self.messages.filter(is_read=False).exclude(sender=user).count()
    
    class Meta:
        unique_together = ['parent', 'teacher']
        ordering = ['-last_message_at']
        verbose_name = "Chat Room"
        verbose_name_plural = "Chat Rooms"


class ChatMessage(models.Model):
    """Individual messages in a chat room"""
    MESSAGE_TYPE_CHOICES = [
        ('text', 'Text'),
        ('image', 'Image'),
        ('file', 'File'),
        ('system', 'System Message'),
    ]
    
    chat_room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Message content
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPE_CHOICES, default='text')
    content = models.TextField()
    
    # Attachments
    image = models.ImageField(upload_to='chat_images/', null=True, blank=True)
    file = models.FileField(upload_to='chat_files/', null=True, blank=True)
    
    # Status
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Edited
    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.sender.get_full_name()}: {self.content[:50]}"
    
    def mark_as_read(self):
        """Mark message as read"""
        from django.utils import timezone
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()
    
    class Meta:
        ordering = ['created_at']
        verbose_name = "Chat Message"
        verbose_name_plural = "Chat Messages"


class Notification(models.Model):
    """Notification system for parents and teachers"""
    NOTIFICATION_TYPES = [
        ('grade_posted', 'Grade Posted'),
        ('attendance_alert', 'Attendance Alert'),
        ('new_announcement', 'New Announcement'),
        ('new_event', 'New Event'),
        ('new_message', 'New Message'),
        ('payment_reminder', 'Payment Reminder'),
        ('general', 'General'),
    ]
    
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    
    title = models.CharField(max_length=200)
    message = models.TextField()
    
    # Link to related object (optional)
    link_url = models.CharField(max_length=500, blank=True)
    
    # Status
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.recipient.get_full_name()} - {self.title}"
    
    def mark_as_read(self):
        from django.utils import timezone
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"