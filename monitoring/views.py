from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse

from users.decorators import teacher_required
from .models import Class, Enrollment, GradeItem, FinalGrade, Attendance


# ========================================
# Class Management
# ========================================

@login_required
@teacher_required
def class_list(request):
    """List all classes taught by teacher"""
    teacher = request.user.teacher_profile
    classes = Class.objects.filter(teacher=teacher).prefetch_related('enrollments')
    
    context = {
        'classes': classes,
        'teacher': teacher,
    }
    return render(request, 'monitoring/class_list.html', context)


@login_required
@teacher_required
def class_detail(request, class_id):
    """View class details"""
    teacher = request.user.teacher_profile
    class_obj = get_object_or_404(Class, id=class_id, teacher=teacher)
    
    context = {
        'class_obj': class_obj,
        'teacher': teacher,
    }
    return render(request, 'monitoring/class_detail.html', context)


@login_required
@teacher_required
def class_students(request, class_id):
    """View students enrolled in class"""
    teacher = request.user.teacher_profile
    class_obj = get_object_or_404(Class, id=class_id, teacher=teacher)
    enrollments = Enrollment.objects.filter(class_obj=class_obj).select_related('student')
    
    context = {
        'class_obj': class_obj,
        'enrollments': enrollments,
        'teacher': teacher,
    }
    return render(request, 'monitoring/class_students.html', context)


# ========================================
# Grade Management
# ========================================

@login_required
@teacher_required
def class_grades(request, class_id):
    """View all grades for a class"""
    teacher = request.user.teacher_profile
    class_obj = get_object_or_404(Class, id=class_id, teacher=teacher)
    
    # Get final grades for all quarters
    final_grades = FinalGrade.objects.filter(
        class_obj=class_obj
    ).select_related('student').order_by('quarter', 'student__last_name')
    
    context = {
        'class_obj': class_obj,
        'final_grades': final_grades,
        'teacher': teacher,
    }
    return render(request, 'monitoring/class_grades.html', context)


@login_required
@teacher_required
def student_grades(request, student_id):
    """View all grades for a specific student"""
    teacher = request.user.teacher_profile
    from users.models import Child
    
    student = get_object_or_404(Child, id=student_id)
    
    # Get all grades for this student in teacher's classes
    grades = FinalGrade.objects.filter(
        student=student,
        class_obj__teacher=teacher
    ).select_related('class_obj').order_by('class_obj', 'quarter')
    
    context = {
        'student': student,
        'grades': grades,
        'teacher': teacher,
    }
    return render(request, 'monitoring/student_grades.html', context)


@login_required
@teacher_required
def upload_grades(request, class_id):
    """Upload grades via Excel file"""
    teacher = request.user.teacher_profile
    class_obj = get_object_or_404(Class, id=class_id, teacher=teacher)
    
    if request.method == 'POST':
        # Handle file upload and processing
        # This would use openpyxl to parse Excel file
        # Similar to your first project's implementation
        
        messages.success(request, 'Grades uploaded successfully!')
        return redirect('monitoring:class_grades', class_id=class_id)
    
    context = {
        'class_obj': class_obj,
        'teacher': teacher,
    }
    return render(request, 'monitoring/upload_grades.html', context)


@login_required
@teacher_required
def download_grade_template(request, class_id):
    """Download Excel template for grade entry"""
    teacher = request.user.teacher_profile
    class_obj = get_object_or_404(Class, id=class_id, teacher=teacher)
    
    # Generate Excel template using openpyxl
    # Similar to your first project's implementation
    
    # For now, return placeholder
    return HttpResponse("Template download - to be implemented with openpyxl")


@login_required
@teacher_required
def edit_grade(request, grade_id):
    """Edit a final grade"""
    teacher = request.user.teacher_profile
    grade = get_object_or_404(FinalGrade, id=grade_id, class_obj__teacher=teacher)
    
    if request.method == 'POST':
        # Handle grade editing
        grade.compute_final_grade()
        messages.success(request, 'Grade updated successfully!')
        return redirect('monitoring:class_grades', class_id=grade.class_obj.id)
    
    context = {
        'grade': grade,
        'teacher': teacher,
    }
    return render(request, 'monitoring/edit_grade.html', context)


# ========================================
# Attendance Management
# ========================================

@login_required
@teacher_required
def attendance_list(request):
    """List attendance records"""
    teacher = request.user.teacher_profile
    
    # Get recent attendance for teacher's classes
    from datetime import date, timedelta
    today = date.today()
    week_ago = today - timedelta(days=7)
    
    attendance = Attendance.objects.filter(
        date__gte=week_ago,
        recorded_by=teacher
    ).select_related('child').order_by('-date')
    
    context = {
        'attendance': attendance,
        'teacher': teacher,
    }
    return render(request, 'monitoring/attendance_list.html', context)


@login_required
@teacher_required
def record_attendance(request):
    """Record attendance for a class"""
    teacher = request.user.teacher_profile
    
    if request.method == 'POST':
        # Handle attendance recording
        messages.success(request, 'Attendance recorded successfully!')
        return redirect('monitoring:attendance_list')
    
    # Get teacher's classes
    classes = Class.objects.filter(teacher=teacher)
    
    context = {
        'classes': classes,
        'teacher': teacher,
    }
    return render(request, 'monitoring/record_attendance.html', context)


@login_required
@teacher_required
def scan_attendance(request):
    """Scan QR codes for attendance"""
    teacher = request.user.teacher_profile
    classes = Class.objects.filter(teacher=teacher)
    
    context = {
        'classes': classes,
        'teacher': teacher,
    }
    return render(request, 'monitoring/scan_attendance.html', context)


@login_required
@teacher_required
def student_attendance(request, student_id):
    """View attendance history for a student"""
    teacher = request.user.teacher_profile
    from users.models import Child
    
    student = get_object_or_404(Child, id=student_id)
    
    # Get attendance records
    attendance = Attendance.objects.filter(
        child=student
    ).order_by('-date')[:30]  # Last 30 days
    
    context = {
        'student': student,
        'attendance': attendance,
        'teacher': teacher,
    }
    return render(request, 'monitoring/student_attendance.html', context)


# ========================================
# Reports
# ========================================

@login_required
@teacher_required
def grade_report(request):
    """Generate grade report"""
    teacher = request.user.teacher_profile
    
    context = {
        'teacher': teacher,
    }
    return render(request, 'monitoring/grade_report.html', context)


@login_required
@teacher_required
def attendance_report(request):
    """Generate attendance report"""
    teacher = request.user.teacher_profile
    
    context = {
        'teacher': teacher,
    }
    return render(request, 'monitoring/attendance_report.html', context)


@login_required
@teacher_required
def class_report(request, class_id):
    """Generate comprehensive class report"""
    teacher = request.user.teacher_profile
    class_obj = get_object_or_404(Class, id=class_id, teacher=teacher)
    
    context = {
        'class_obj': class_obj,
        'teacher': teacher,
    }
    return render(request, 'monitoring/class_report.html', context)