from django.urls import path
from . import views

app_name = 'monitoring'

urlpatterns = [
    # ========================================
    # Class Management (Teacher)
    # ========================================
    path('classes/', views.class_list, name='class_list'),
    path('class/<int:class_id>/', views.class_detail, name='class_detail'),
    path('class/<int:class_id>/students/', views.class_students, name='class_students'),
    
    # ========================================
    # Grade Management (Teacher)
    # ========================================
    path('class/<int:class_id>/grades/', views.class_grades, name='class_grades'),
    path('class/<int:class_id>/upload-grades/', views.upload_grades, name='upload_grades'),
    path('class/<int:class_id>/download-template/', views.download_grade_template, name='download_grade_template'),
    path('student/<int:student_id>/grades/', views.student_grades, name='student_grades'),
    path('grade/<int:grade_id>/edit/', views.edit_grade, name='edit_grade'),
    
    # ========================================
    # Attendance Management (Teacher)
    # ========================================
    path('attendance/', views.attendance_list, name='attendance_list'),
    path('attendance/record/', views.record_attendance, name='record_attendance'),
    path('attendance/scan/', views.scan_attendance, name='scan_attendance'),
    path('student/<int:student_id>/attendance/', views.student_attendance, name='student_attendance'),
    
    # ========================================
    # Reports (Teacher)
    # ========================================
    path('reports/grades/', views.grade_report, name='grade_report'),
    path('reports/attendance/', views.attendance_report, name='attendance_report'),
    path('class/<int:class_id>/report/', views.class_report, name='class_report'),
]