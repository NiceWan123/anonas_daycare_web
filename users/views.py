from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout as django_logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import Teacher, Parent, Child
from .forms import (
    TeacherLoginForm, 
    ParentLoginForm,
    ParentProfileUpdateForm
)
from .decorators import teacher_required, parent_required


# ========================================
# Login Selection & Common Views
# ========================================

def login_selection(request):
    """Main login page - user selects role (Parent or Teacher)"""
    if request.user.is_authenticated:
        return redirect_to_dashboard(request.user)
    return render(request, 'users/login_selection.html')


def redirect_to_dashboard(user):
    """Redirect user to appropriate dashboard based on role"""
    if user.role == 'teacher':
        return redirect('users:teacher_dashboard')
    elif user.role == 'parent':
        return redirect('users:parent_dashboard')
    elif user.role == 'admin':
        return redirect('admin:index')
    return redirect('users:login_selection')


def logout_view(request):
    """Logout user and redirect to login selection"""
    django_logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('users:login_selection')


# ========================================
# Teacher Authentication & Dashboard
# ========================================

def teacher_login(request):
    """Teacher login with username and password"""
    if request.user.is_authenticated:
        return redirect('users:teacher_dashboard')

    form = TeacherLoginForm(request.POST or None)
    error = None

    if form.is_valid():
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        user = authenticate(request, username=username, password=password)

        if user is not None and user.role == 'teacher':
            login(request, user)
            messages.success(request, f'Welcome back, {user.get_full_name()}!')
            return redirect('users:teacher_dashboard')
        else:
            error = "Invalid credentials or not a teacher account."

    return render(request, 'users/teacher_login.html', {
        'form': form,
        'error': error
    })


@login_required
@teacher_required
def teacher_dashboard(request):
    """Teacher dashboard view"""
    teacher = request.user.teacher_profile
    
    # Get statistics
    from monitoring.models import Class, GradeItem, FinalGrade
    from information.models import Announcement
    
    # Classes taught by this teacher
    classes = Class.objects.filter(teacher=teacher)
    total_classes = classes.count()
    
    # Total students across all classes
    from monitoring.models import Enrollment
    total_students = Enrollment.objects.filter(class_obj__in=classes).values('student').distinct().count()
    
    # Recent grade items posted
    recent_grades = GradeItem.objects.filter(
        class_obj__teacher=teacher
    ).select_related('student', 'class_obj').order_by('-created_at')[:10]
    
    # Teacher's announcements
    announcements = Announcement.objects.filter(
        posted_by=teacher
    ).order_by('-created_at')[:5]
    
    context = {
        'teacher': teacher,
        'classes': classes,
        'total_classes': total_classes,
        'total_students': total_students,
        'recent_grades': recent_grades,
        'announcements': announcements,
    }
    
    return render(request, 'users/teacher_dashboard.html', context)


# ========================================
# Parent Authentication & Dashboard
# ========================================

def parent_login(request):
    """Parent login with username and password"""
    if request.user.is_authenticated:
        return redirect('users:parent_dashboard')

    form = ParentLoginForm(request.POST or None)
    error = None

    if form.is_valid():
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        user = authenticate(request, username=username, password=password)

        if user is not None and user.role == 'parent':
            login(request, user)
            messages.success(request, f'Welcome back, {user.get_full_name()}!')
            return redirect('users:parent_dashboard')
        else:
            error = "Invalid credentials or not a parent account."

    return render(request, 'users/parent_login.html', {
        'form': form,
        'error': error
    })


@login_required
@parent_required
def parent_dashboard(request):
    """Parent dashboard view"""
    parent = request.user.parent_profile
    
    # Get all children
    children = parent.children.all()
    
    # Get data for each child
    from monitoring.models import FinalGrade, Attendance
    from information.models import Announcement, Event
    from datetime import date
    
    children_data = []
    for child in children:
        # Latest final grades
        latest_grades = FinalGrade.objects.filter(
            student=child
        ).select_related('class_obj').order_by('-quarter', '-updated_at')[:5]
        
        # Recent attendance (last 10 days)
        recent_attendance = Attendance.objects.filter(
            child=child
        ).order_by('-date')[:10]
        
        # Calculate attendance stats for current month
        current_month_attendance = Attendance.objects.filter(
            child=child,
            date__month=date.today().month,
            date__year=date.today().year
        )
        
        total_days = current_month_attendance.count()
        present_days = current_month_attendance.filter(status='present').count()
        attendance_rate = (present_days / total_days * 100) if total_days > 0 else 0
        
        children_data.append({
            'child': child,
            'latest_grades': latest_grades,
            'recent_attendance': recent_attendance,
            'attendance_stats': {
                'total_days': total_days,
                'present_days': present_days,
                'attendance_rate': round(attendance_rate, 1)
            }
        })
    
    # School announcements for parents
    announcements = Announcement.objects.filter(
        is_published=True,
        target_audience__in=['all', 'parents']
    ).order_by('-created_at')[:5]
    
    # Upcoming events
    events = Event.objects.filter(
        is_active=True,
        start_date__gte=date.today()
    ).order_by('start_date')[:5]
    
    context = {
        'parent': parent,
        'children_data': children_data,
        'announcements': announcements,
        'events': events,
    }
    
    return render(request, 'users/parent_dashboard.html', context)


# ========================================
# Profile Management
# ========================================

@login_required
@parent_required
def parent_profile(request):
    """Parent profile view and edit"""
    parent = request.user.parent_profile
    
    if request.method == 'POST':
        form = ParentProfileUpdateForm(request.POST, request.FILES, instance=parent)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('users:parent_profile')
    else:
        form = ParentProfileUpdateForm(instance=parent)
    
    return render(request, 'users/parent_profile.html', {
        'parent': parent,
        'form': form
    })


# ========================================
# Child Details View (for Parents)
# ========================================

@login_required
@parent_required
def child_detail(request, child_id):
    """Detailed view of a child's information for parent"""
    parent = request.user.parent_profile
    
    # Ensure parent has access to this child
    try:
        child = Child.objects.get(id=child_id, parents=parent)
    except Child.DoesNotExist:
        messages.error(request, 'Child not found or you do not have access.')
        return redirect('users:parent_dashboard')
    
    from monitoring.models import FinalGrade, Attendance, Class, Enrollment
    
    # Get all enrolled classes
    enrolled_classes = Class.objects.filter(enrollments__student=child)
    
    # All final grades grouped by quarter
    grades_by_quarter = {}
    for quarter in range(1, 5):
        grades = FinalGrade.objects.filter(
            student=child,
            quarter=quarter
        ).select_related('class_obj')
        if grades.exists():
            grades_by_quarter[quarter] = grades
    
    # Attendance records (last 30 days)
    attendance = Attendance.objects.filter(
        child=child
    ).order_by('-date')[:30]
    
    # Attendance summary
    from datetime import date, timedelta
    thirty_days_ago = date.today() - timedelta(days=30)
    recent_attendance = Attendance.objects.filter(
        child=child,
        date__gte=thirty_days_ago
    )
    
    total_days = recent_attendance.count()
    present_days = recent_attendance.filter(status='present').count()
    absent_days = recent_attendance.filter(status='absent').count()
    late_days = recent_attendance.filter(status='late').count()
    
    context = {
        'child': child,
        'enrolled_classes': enrolled_classes,
        'grades_by_quarter': grades_by_quarter,
        'attendance': attendance,
        'attendance_summary': {
            'total_days': total_days,
            'present_days': present_days,
            'absent_days': absent_days,
            'late_days': late_days,
            'attendance_rate': round((present_days / total_days * 100) if total_days > 0 else 0, 1)
        }
    }
    
    return render(request, 'users/child_detail.html', context)


# ========================================
# Teacher - View Classes and Students
# ========================================

@login_required
@teacher_required
def teacher_classes(request):
    """View all classes taught by teacher"""
    teacher = request.user.teacher_profile
    classes = Class.objects.filter(teacher=teacher).prefetch_related('enrollments__student')
    
    context = {
        'teacher': teacher,
        'classes': classes,
    }
    
    return render(request, 'users/teacher_classes.html', context)


@login_required
@teacher_required
def class_detail(request, class_id):
    """View students in a specific class"""
    teacher = request.user.teacher_profile
    
    from monitoring.models import Class, Enrollment
    
    # Ensure teacher owns this class
    try:
        class_obj = Class.objects.get(id=class_id, teacher=teacher)
    except Class.DoesNotExist:
        messages.error(request, 'Class not found or you do not have access.')
        return redirect('users:teacher_classes')
    
    # Get enrolled students
    enrollments = Enrollment.objects.filter(
        class_obj=class_obj
    ).select_related('student').order_by('student__last_name', 'student__first_name')
    
    context = {
        'teacher': teacher,
        'class_obj': class_obj,
        'enrollments': enrollments,
    }
    
    return render(request, 'users/class_detail.html', context)