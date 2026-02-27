from django.shortcuts import render, redirect, get_object_or_404
from .forms import *
from .models import *
from django.contrib import messages
from django.db.models import Q
from datetime import date 
from django.http import HttpResponse, JsonResponse
from django.http import HttpResponseNotFound
import re
import cv2
import numpy as np
import requests
import json
from PyPDF2 import PdfReader
from django.core.files.storage import default_storage
import os
import tempfile
import fitz 
from PIL import Image
from google import genai

NVIDIA_API_KEY = "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"
# Configure Gemini API Key (Ideally this should be in .env, but hardcoding for now as per instructions/assumptions)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyANUm5NhkC12yWPW3fR5Kf5NO4vC26ZVCw") # User provided key
client = genai.Client(api_key=GEMINI_API_KEY)
NVIDIA_API_KEY = "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"
CHOICES = ['A', 'B', 'C', 'D']
def main(request):
    teachers = teacherreg.objects.filter(login_id__status='1')
    return render(request, 'main.html', {'teachers': teachers})
def admin(request):
    user_count = Studentreg.objects.all().count()
    t_count = teacherreg.objects.all().count()
    return render(request, 'admin.html',{'user_count': user_count,'t_count':t_count})
def user(request):
    results = exam.objects.all()
    teachers = teacherreg.objects.filter(login_id__status='1')
    return render(request, 'user.html', {'data': results, 'teachers': teachers})
def tuser(request):
    teachers = teacherreg.objects.filter(login_id__status='1')
    return render(request, 'tuser.html', {'teachers': teachers})
def studentreg(request):
    if request.method == 'POST':
        form=studentform(request.POST,request.FILES)
        logins=loginform(request.POST)
        print(form)
        if form.is_valid() and logins.is_valid():
            a=logins.save(commit=False)
            a.usertype=1
            a.save()
            b=form.save(commit=False)
            b.login_id=a
            b.save()
            messages.success(request,"Form successfully submitted")
        return redirect('main')
    else:
        form=studentform()
        logins=loginform()
    return render(request,'studentreg.html',{'form':form,'login':logins})

def adminstudview(request):
    view_id=Login.objects.filter(usertype=1).select_related('student_as_loginid')
    return render(request,'adminstudview.html',{'data':view_id})
def rejects(request,id):
    a=get_object_or_404(Login,id=id)
    a.status=2
    a.save()
    return redirect('searchstudad')
def approves(request, id):
    a = get_object_or_404(Login, id=id)
    a.status = 1
    a.save()
    return redirect('searchstudad')


def adminteachview(request):
    view_id=Login.objects.filter(usertype=2).select_related('t')
    return render(request,'adminteachview.html',{'data':view_id})
def rejectt(request,id):
    a=get_object_or_404(Login,id=id)
    a.status=2
    a.save()
    return redirect('adminteachview')
def approvet(request,id):
    a=get_object_or_404(Login,id=id)
    a.status=1
    a.save()
    return redirect('adminteachview')



def teacherregister(request):
    if request.method == 'POST':
        form = teacherform(request.POST,request.FILES)
        logins = loginform(request.POST)
        print(form)
        if form.is_valid() and logins.is_valid():
            
            a = logins.save(commit=False)
            a.usertype = 2  
            a.save()
            b = form.save(commit=False)
            b.login_id = a  
            b.save()
            
            
            messages.success(request, "Form successfully submitted")
            return redirect('main') 
    else:
        form = teacherform()
        logins=loginform()
    return render(request,'teacherreg.html',{'form':form,'login':logins})
def login(request):
    print("DEBUG: Login view called")
    if request.method == 'POST':
        print("DEBUG: POST request received")
        form = login_check(request.POST)
        if form.is_valid():
            print("DEBUG: Form is valid")
            username = form.cleaned_data['username']
            password = form.cleaned_data['password'].strip()  # Clean whitespace
            print(f"DEBUG: Attempting login for username: {username}")
            try:
                user = Login.objects.get(username=username)
                print(f"DEBUG: User found: {user.username}, usertype: {user.usertype}, status: {user.status}")
                if user.password.strip() == password:  # Compare stripped values
                    print("DEBUG: Password matched")
                    # Only check status for students and teachers
                    if user.usertype in [1, 2]:
                        if user.status == 2:
                            print("DEBUG: Account rejected")
                            messages.error(request, 'Your account has been rejected.')
                            return redirect('login')
                        elif user.status == 0:
                            print("DEBUG: Account under review")
                            messages.error(request, 'Your account is under review. Please wait for admin approval.')
                            return redirect('login')

                    # User is allowed to log in
                    if user.usertype == 1:
                        print("DEBUG: Redirecting to user")
                        request.session['stud_id'] = user.id
                        return redirect('user')
                    elif user.usertype == 2:
                        print("DEBUG: Redirecting to tuser")
                        request.session['t_id'] = user.id
                        return redirect('tuser')
                    elif user.usertype == 3:
                        print("DEBUG: Redirecting to admin")
                        request.session['a_id'] = user.id
                        return redirect('admin')
                    else:
                        print(f"DEBUG: Unknown usertype: {user.usertype}")
                else:
                    print(f"DEBUG: Password mismatch. Input: {password}, Stored: {user.password}")
                    messages.error(request, 'Invalid password')
            except Login.DoesNotExist:
                print("DEBUG: User does not exist")
                messages.error(request, 'User does not exist')
        else:
            print(f"DEBUG: Form errors: {form.errors}")
    else:
        print("DEBUG: GET request")
        form = login_check()
    return render(request, 'login.html', {'login': form})

def sprofile(request):
    stud_id=request.session.get('stud_id')   
    login_details=get_object_or_404(Login,id=stud_id)
    stud=get_object_or_404(Studentreg,login_id=stud_id)
    if request.method=='POST':
        form=studentform(request.POST,request.FILES,instance=stud)
        form2=loginform(request.POST, instance=login_details)
        if form.is_valid() and form2.is_valid():
            form.save()
            form2.save()
            return redirect('user')
    else:
        form=studentform(instance=stud)
        form2=loginform( instance=login_details)

    return render(request, 'sprofile.html',{'form':form,'form2':form2})

def tprofile(request):
    t_id=request.session.get('t_id')   
    login_details=get_object_or_404(Login,id=t_id)
    teacher=get_object_or_404(teacherreg,login_id=t_id)
    if request.method=='POST':
        form=teacherform(request.POST,request.FILES,instance=teacher)
        form2=loginform(request.POST, instance=login_details)
        if form.is_valid() and form2.is_valid():
            form.save()
            form2.save()
            return redirect('tuser')
    else:
        form=teacherform(instance=teacher)
        form2=loginform( instance=login_details)

    return render(request, 'tprofile.html',{'form':form,'form2':form2})

def studentsview(request):
    view_id=Studentreg.objects.all()
    return render(request,'studentsview.html',{'data':view_id})

def search_student(request):
    query = request.GET.get('q', '') 
    results = Studentreg.objects.all()  

    if query:
        results = results.filter(
           Q(admno__icontains=query)|
           Q(name__icontains=query)|
           Q(department__icontains=query)  
        )

    return render(request, 'studentsview.html', {'results': results, 'query': query})

def teachersview(request):
    query = request.GET.get('q')  # Get the search query from the input field
    teachers = teacherreg.objects.filter(
        login_id__status='1',
        login_id__usertype=2
    )

    if query:
        teachers = teachers.filter(
            Q(tname__icontains=query) | Q(tdepartment__icontains=query)
        )

    return render(request, 'teachersview.html', {'data': teachers})

def search_teacher(request):
    query = request.GET.get('q', '') 
    results = teacherreg.objects.all()  

    if query:
        results = results.filter(
           Q(tdepartment__icontains=query)|
           Q(tname__icontains=query)
        )

    return render(request, 'teachersview.html', {'results': results, 'query': query})

def uploadessay(request,id):
    stud_id=request.session.get('stud_id')   
    login_details=get_object_or_404(Login,id=stud_id)
    te_id=get_object_or_404(teacherreg,id=id)
    stud = get_object_or_404(Studentreg,login_id = stud_id)
    if request.method=='POST':
        form=essayuploadform(request.POST,request.FILES)
        if form.is_valid():
            a=form.save(commit=False)
            a.login_id=login_details
            a.student = stud
            a.tea_id=te_id
            a.save()
            return redirect('user')
    else:
        form=essayuploadform()
    return render(request, 'uploadessay.html',{'form':form})

def viewessay(request):
    stud_id=request.session.get('stud_id')
    login_details=get_object_or_404(Login,id=stud_id)
    view_id=Essay.objects.filter(login_id=login_details)
    return render(request,'viewessay.html',{'data':view_id})

def removeessay(request,id):
    a=get_object_or_404(Essay,id=id)
    a.delete()
    return redirect('viewessay')

def viewessayt(request):
   tea_id=request.session.get('t_id')
   login_details=get_object_or_404(teacherreg,login_id=tea_id)
   view_id=Essay.objects.filter(tea_id = login_details).select_related('login_id__student_as_loginid')
   return render(request, 'viewessayt.html', {'view_essay': view_id})

def removeessayt(request,id):
    b=get_object_or_404(Essay,id=id)
    b.delete()
    return redirect('viewessayt')



def uploadanswer(request,id):
    stud_id=request.session.get('stud_id')   
    login_details=get_object_or_404(Login,id=stud_id)
    tea_id=get_object_or_404(teacherreg,id=id)
    if request.method=='POST':
        form=answersheet(request.POST,request.FILES)
        if form.is_valid():
            a=form.save(commit=False)
            a.login_id=login_details
            a.t_id=tea_id
            a.save()
            return redirect('user')
    else:
        form=answersheet()
    return render(request, 'uploadanswer.html',{'form':form})
def viewanswer(request):
    stud_id=request.session.get('stud_id')
    login_details=get_object_or_404(Login,id=stud_id)
    view_id=Answer.objects.filter(login_id=login_details)
    return render(request,'viewanswer.html',{'data':view_id})
def removeanswer(request,id):
    a=get_object_or_404(Answer,id=id)
    a.delete()
    return redirect('viewanswer')
def viewanswert(request):
    tea_id=request.session.get('t_id')
    login_details=get_object_or_404(teacherreg,login_id=tea_id)
    view_id=Answer.objects.filter(t_id = login_details).select_related('login_id__student_as_loginid')
   
    return render(request, 'viewanswert.html', {'view_ans': view_id})

def removeanswert(request,id):
    b=get_object_or_404(Answer,id=id)
    b.delete()
    return redirect('viewanswert')


def viewomr(request):
    stud_id=request.session.get('stud_id')
    login_details=get_object_or_404(Login,id=stud_id)
    view_id=Omr.objects.filter(login_id=login_details)
    return render(request,'viewomr.html',{'data':view_id})

def removeomr(request,id):
    a=get_object_or_404(Omr,id=id)
    a.delete()
    return redirect('viewomr')

def viewomrt(request):
    tea_id=request.session.get('t_id')
    login_details=get_object_or_404(teacherreg,login_id=tea_id)
    view_id=Omr.objects.filter(tc_id = login_details).select_related('login_id__student_as_loginid')
    # print(view_id)
   
    return render(request, 'viewomrt.html', {'view_omr': view_id})

def removeomrt(request,id):
    b=get_object_or_404(Omr,id=id)
    b.delete()
    return redirect('viewomrt')

def uploadassignment(request,id):
    stud_id=request.session.get('stud_id')   
    student_obj=get_object_or_404(Studentreg,login_id=stud_id)
    question_obj = get_object_or_404(AssignmentQuestion, id=id)
    tc_id = question_obj.teacher
    
    if request.method=='POST':
        form=assignment(request.POST,request.FILES)
        if form.is_valid():
            a=form.save(commit=False)
            a.login_id=student_obj
            a.ta_id=tc_id
            a.question = question_obj
            
            # Extract and Rate
            transcription = extract_handwriting_with_gemini(request.FILES['assignment'])
            a.transcription = transcription
            a.rating = rate_assignment_with_ai(transcription, question_obj.question_text)
            
            a.save()
            messages.success(request, f"Assignment '{question_obj.title}' uploaded and rated successfully!")
            return redirect('user')
    else:
        form=assignment()
    return render(request, 'uploadassignment.html',{'form':form, 'question': question_obj})

def add_assignment_view(request):
    tea_id = request.session.get('t_id')
    teacher = get_object_or_404(teacherreg, login_id=tea_id)
    if request.method == 'POST':
        form = AssignmentQuestionForm(request.POST)
        if form.is_valid():
            a = form.save(commit=False)
            a.teacher = teacher
            a.save()
            messages.success(request, "Assignment added successfully.")
            return redirect('tuser')
    else:
        form = AssignmentQuestionForm()
    return render(request, 'add_assignment.html', {'form': form})

def student_assignments_view(request):
    assignments = AssignmentQuestion.objects.all()
    return render(request, 'student_assignments.html', {'assignments': assignments})

def rate_assignment_with_ai(transcription, question_text):
    prompt = f"""
    Evaluate the following student's handwritten transcription against the assignment question.
    Provide a rating (Excellent, Good, Average, or Poor) and a short one-sentence feedback.
    
    Assignment Question: {question_text}
    Student Submission: {transcription}
    
    Format: [Rating] : [Feedback]
    """
    try:
        response = client.models.generate_content(
            model='gemini-flash-latest',
            contents=[prompt]
        )
        return response.text
    except Exception as e:
        print(f"Rating error: {e}")
        return "Rating unavailable"

def viewassignment(request):
    stud_id=request.session.get('stud_id')
    student_obj=get_object_or_404(Studentreg,login_id=stud_id)
    submissions = Assignment.objects.filter(login_id=student_obj).select_related('question')

    return render(request,'viewassignment.html',{'submissions':submissions})

def removeassignment(request):
    stud_id=request.session.get('stud_id')
    login_details=get_object_or_404(Login,id=stud_id)
    view_id=Assignment.objects.filter(login_id=login_details)
    return render(request,'viewassignment.html',{'data':view_id})

def viewassignmentt(request):
    tea_id = request.session.get('t_id')
    teacher_obj = get_object_or_404(teacherreg, login_id=tea_id)
    submissions = Assignment.objects.filter(ta_id=teacher_obj).select_related('login_id', 'question') 
    
    query = request.GET.get('q', '') 
    if query:
        submissions = submissions.filter(
           Q(login_id__admno__icontains=query) |
           Q(login_id__name__icontains=query) |
           Q(login_id__department__icontains=query) |
           Q(question__title__icontains=query)
        )
    return render(request, 'viewassignmentt.html', {'submissions': submissions, 'query':query})

def upload_assignment_mark(request, id):
    assignments = get_object_or_404(Assignment, id=id)

    if request.method == 'POST':
        form = assignment(request.POST, instance=assignments)
        if form.is_valid():
            form.save()
            return redirect('viewassignmentt')  # Replace with your actual list view
    else:
        form = assignment(instance=assignments)

    return render(request, 'assignmentmark.html', {'form': form, 'student': assignments.login_id})


def removeassignmentt(request,id):
    b=get_object_or_404(Assignment,id=id)
    b.delete()
    return redirect('viewassignmentt')

def viewattendance(request):
    form=attendance()
    dept = request.GET.get('department') 
    sem = request.GET.get('semester') 
    results = Studentreg.objects.filter(department=dept,semester=sem) 
    if results:
        return render(request, 'attendancetable.html',{'results':results})
    print(results)
    return render(request, 'attendance.html',{'form':form})

def present(request,id):
    a=get_object_or_404(Studentreg,id=id)
    tea_id = request.session.get('t_id')
    login_details = get_object_or_404(teacherreg, login_id=tea_id)
    if Attendance.objects.filter(t_id= login_details,login_id=a,present=1,current_date=date.today()).exists():
        return JsonResponse({'status': 'error', 'message': ' Attendance Already marked for today!'})
    else:
        Attendance.objects.create(t_id= login_details,login_id=a,present=1)
        return JsonResponse({'status': 'success', 'message': 'Attendance marked Now!'})


def absent(request,id):
    a=get_object_or_404(Studentreg,id=id)
    tea_id = request.session.get('t_id')
    login_details = get_object_or_404(teacherreg, login_id=tea_id)
    if Attendance.objects.filter(t_id= login_details,login_id=a,absent=2,current_date=date.today()).exists():
        return JsonResponse({'status': 'error', 'message': ' Attendance Already marked for today!'})
    else:
        Attendance.objects.create(t_id= login_details,login_id=a,absent=2)
        return JsonResponse({'status': 'success', 'message': 'Attendance marked Now!'})

def attendanceviewt(request):
    form=attendanceview()
    date = request.GET.get('date') 
    results = Attendance.objects.filter(current_date=date,present=1) 
    if results:
        return render(request, 'attendancet.html',{'results':results})
    print(results)
    return render(request,'checkattendance.html',{'form':form})

def markupload(request):
    form=attendance()
    dept = request.GET.get('department') 
    sem = request.GET.get('semester') 
    results = Studentreg.objects.filter(department=dept,semester=sem) 
    if results:
        return render(request, 'attendancetable.html',{'results':results})
    print(results)
    return render(request, 'attendance.html',{'form':form})


# def adminsubjects(request):
#     if request.method == 'POST':
#         dept = request.POST.get('dept')
#         sem = request.POST.get('sem')
#         courses = request.POST.getlist('courses[]')  # Get all courses
#         elective_courses = request.POST.getlist('elective_courses[]')  # Get electives

#         if len(elective_courses) != 3:  # Ensure exactly 3 elective courses
#             messages.error(request, "You must enter exactly 3 elective courses.")
#             return redirect('admin')

#         # Create Subject (semester)
#         subject = Subject.objects.create(dept=dept, sem=sem)

#         # Save each regular course
#         for course_name in courses:
#             if course_name.strip():
#                 Course.objects.create(subject=subject, name=course_name)

#         # Save exactly 3 elective courses
#         for elective_name in elective_courses:
#             if elective_name.strip():
#                 ElectiveCourse.objects.create(subject=subject, name=elective_name)

#         messages.success(request, "Subject and courses added successfully.")
#         return redirect('admin')

#     else:
#         form = SubjectForm()  
#     return render(request, 'subjects.html', {'form': form})




def adminsubjects(request):
    form = SubjectForm()          # Ensure form is initialized
    detail_form = SubjectDetailForm()
    if request.method == 'POST':
        if 'select_dept_sem' in request.POST:
            dept = request.POST.get('dept')
            sem = request.POST.get('sem')

            if dept and sem:
                return render(request, 'subjects.html', {
                    'dept': dept,
                    'sem': sem,
                    'form': SubjectForm(),
                    'detail_form': SubjectDetailForm()
                })
            else:
                messages.error(request, "Please select both Department and Semester.")
                return redirect('adminsubjects')

        elif 'add_subject' in request.POST:
            dept = request.POST.get('dept')
            sem = request.POST.get('sem')

            # Create Subject
            subject = Subject.objects.create(dept=dept, sem=sem)

            # Handle Subject Details
            detail_form = SubjectDetailForm(request.POST)
            if detail_form.is_valid():
                subject_detail = detail_form.save(commit=False)
                subject_detail.subject = subject
                subject_detail.save()
                messages.success(request, "Subject and details added successfully.")
                return redirect('adminsubjects')
            else:
                messages.error(request, "Please correct the errors in the form.")

    else:
        form = SubjectForm()
        detail_form = SubjectDetailForm()

    return render(request, 'subjects.html', {'form': form, 'detail_form': detail_form})



# def subchoice(request):
#     stud_id = request.session.get('stud_id')
#     login_details = get_object_or_404(Studentreg, login_id=stud_id)
#     semester=login_details.semester
#     print(semester)
#     return render(request, 'subchoicestud.html')


def subchoice(request):
    stud_id = request.session.get('stud_id')  # Get student ID from session
    student = get_object_or_404(Studentreg, login_id=stud_id)  # Fetch student

    if request.method == 'POST':
        form = ElectiveForm(request.POST, student=student)
        if form.is_valid():
            # Ensure student hasn't already selected an elective for the semester
            if SubjectView.objects.filter(stud_id=student, semester=student.semester).exists():
                return render(request, 'subchoicestud.html', {
                    'form': form, 
                    'error': 'You have already selected an elective for this semester!'
                })

            # Save elective choice
            subject_view = form.save(commit=False)
            subject_view.stud_id = student
            subject_view.semester = student.semester
            subject_view.save()
            return redirect('user')  # Redirect to success page after submission

    else:
        form = ElectiveForm(student=student)

    return render(request, 'subchoicestud.html', {'form': form})

def uploadmarks(request):
    form=uploadmark()
    dept = request.GET.get('department') 
    sem = request.GET.get('semester') 
    print(dept)
    
    results = Studentreg.objects.filter(department=dept,semester=sem) 
    if results:
        return render(request, 'markuploadviewt.html',{'results':results})
    print(results)
    return render(request, 'markupload.html',{'form':form})



# def upload_internal_marks(request, course_id, student_id):
#     # Fetch the course, student, and subject
#     course = get_object_or_404(Course, id=course_id)
#     student = get_object_or_404(Studentreg, id=student_id)
#     subject = course.id  # Fetch the correct subject from the course
#     logid = request.session.get('t_id')
#     teacher_id = get_object_or_404(teacherreg, login_id=logid)

#     # Check if marks already exist for this student and subject
#     existing_marks = InternalMarks.objects.filter(subject=subject, stud_id=student).exists()

#     if request.method == 'POST':
#         marks = request.POST.get('marks')  # Get the marks from the form input

#         # Validate marks (ensure it's a numeric value)
#         if not marks.isdigit():
#             messages.error(request, "Marks must be a numeric value.")
#             return redirect('internals', course_id=course_id, student_id=student_id)

#         marks = int(marks)  # Convert marks to integer

#         if existing_marks:
#             # If marks already exist for the student and subject, prevent duplicate entry
#             messages.error(request, 'Marks for this student in this subject already exist.')
#         else:
#             # Create a new entry
#             InternalMarks.objects.create(subject_id=subject, stud_id=student, marks=marks, login_id=teacher_id)
#             messages.success(request, 'Marks uploaded successfully!')

#         return redirect('viewsubjectt', student.id)  # Redirect after saving

#     # If GET request, render the form
#     return render(request, 'uploadmark_teacher.html', {'course': course, 'student': student})

# def upload_internal_marks_elective(request, course_id, student_id):
#     # Fetch the course, student, and subject
#     course = get_object_or_404(ElectiveCourse, id=course_id)
#     student = get_object_or_404(Studentreg, id=student_id)
#     subject = course.id  # Fetch the correct subject from the course
#     logid = request.session.get('t_id')
#     teacher_id = get_object_or_404(teacherreg, login_id=logid)

#     # Check if marks already exist for this student and subject
#     existing_marks = InternalMarks.objects.filter(subject=subject, stud_id=student).exists()

#     if request.method == 'POST':
#         marks = request.POST.get('marks')  # Get the marks from the form input

#         # Validate marks (ensure it's a numeric value)
#         if not marks.isdigit():
#             messages.error(request, "Marks must be a numeric value.")
#             return redirect('internals', course_id=course_id, student_id=student_id)

#         marks = int(marks)  # Convert marks to integer

#         if existing_marks:
#             # If marks already exist for the student and subject, prevent duplicate entry
#             messages.error(request, 'Marks for this student in this subject already exist.')
#         else:
#             # Create a new entry
#             InternalMarks.objects.create(subject_id=subject, stud_id=student, marks=marks, login_id=teacher_id)
#             messages.success(request, 'Marks uploaded successfully!')

#         return redirect('viewsubjectt', student.id)  # Redirect after saving

#     # If GET request, render the form
#     return render(request, 'uploadmark_teacher.html', {'course': course, 'student': student})


# def viewsubject(request):
#     # Get the student ID from the session (assuming the user is linked to the Studentreg model)
#     student_id = request.session.get('stud_id')
#     st = get_object_or_404(Studentreg, login_id=student_id)

#     # Get all subjects for the student based on their department and semester
#     subjects = Subject.objects.filter(dept=st.department, sem=st.semester)

#     # Get all the courses (core subjects) for the student's semester
#     courses = Course.objects.filter(subject__in=subjects)

#     # Get the electives selected by the student for the current semester from the SubjectView model
#     selected_electives = SubjectView.objects.filter(stud_id=st, semester=st.semester)
#     electives = ElectiveCourse.objects.filter(name__in=[selection.elective_course for selection in selected_electives])

#     # Get the student's marks for the courses and electives from the InternalMarks model
#     course_marks = InternalMarks.objects.filter(stud_id=st.id, subject__in=[course.id for course in courses])
#     elective_marks = InternalMarks.objects.filter(stud_id=st.id, subject__in=[elective.id for elective in electives])

#     # Attach marks to courses and electives
#     for course in courses:
#         course.marks = None  # Default to None if no marks found
#         for mark in course_marks:
#             if mark.subject == course:
#                 course.marks = mark.marks
#                 break

#     for elective in electives:
#         elective.marks = None  # Default to None if no marks found
#         for mark in elective_marks:
#             if mark.subject == elective:
#                 elective.marks = mark.marks
#                 break

#     # Pass the data to the template
#     return render(request, 'viewsubject.html', {
#         'student': st,  # Pass the student details
#         'courses': courses,
#         'electives': electives,
#     })

# def viewsubjectt(request, id):
#     student = get_object_or_404(Studentreg, id=id)

#     # Check if data is being returned
#     core_subjects = Course.objects.filter(subject__dept=student.department, subject__sem=student.semester)
#     print("Core Subjects:", core_subjects)  # Debugging line

#     electives = SubjectView.objects.filter(stud_id=student, semester=student.semester)
#     print("Electives:", electives)  # Debugging line

#     view_sub = ElectiveCourse.objects.filter(name__in=[elective.elective_course for elective in electives])
#     print("View Sub:", view_sub)  # Debugging line

#     internal_marks = InternalMarks.objects.filter(stud_id=student)
#     print("Internal Marks:", internal_marks)  # Debugging line

#     return render(request, 'viewsubjectt.html', {
#         'studentid': student.id,
#         'core_subjects': core_subjects,
#         'view_sub': view_sub,
#         'internal_marks': internal_marks,
#     })

def viewsubjectt(request, id):
    student = get_object_or_404(Studentreg, id=id)

    # Get the student's subject selection
    selection = StudentSubjectSelection.objects.filter(student=student).first()

    # Extract core subjects from related SubjectDetail
    core_subjects = []
    if selection and selection.subject:
        subject_detail = selection.subject
        for field in ['major1', 'major2', 'major3']:
            field_value = getattr(subject_detail, field, None)
            if field_value:
                core_subjects.extend([sub.strip() for sub in field_value.split(',') if sub.strip()])

    return render(request, 'viewsubjectt.html', {
        'student': student,
        'selection': selection,
        'core_subjects': core_subjects,
    })




# def viewsubjectt(request, id):
#     # Get student details
#     student = get_object_or_404(Studentreg, id=id)

#     # Get the subject (based on department & semester)
#     subject = get_object_or_404(Subject, dept=student.department, sem=student.semester)

#     # Fetch core subjects
#     core_subjects = Course.objects.filter(subject=subject)

#     # Fetch electives chosen by student
#     selected_electives = SubjectView.objects.filter(stud_id=student)

#     # Fetch internal marks for the student
#     internal_marks = InternalMarks.objects.filter(stud_id=student)

#     return render(request, 'viewsubjectt.html', {
#         'core_subjects': core_subjects,
#         'view_sub': selected_electives,  # Corrected this line
#         'internal_marks': internal_marks,
#         'studentid': id  # Use id, not undefined student_id
#     })

def promote(request,id):
    student = get_object_or_404(Studentreg, id=id)
    sem=student.semester
    student.semester=sem+1
    student.save()
    
    return redirect('adminstudview')

def demote(request,id):
    student = get_object_or_404(Studentreg, id=id)
    sem=student.semester
    student.semester=sem-1
    student.save()
    return redirect('adminstudview')

def studattendance(request):
    stud_id = request.session.get('stud_id')
    print(stud_id)
    student = get_object_or_404(Studentreg, login_id=stud_id) 
    print(student)
    attendance = Attendance.objects.filter(login_id=student)
    perc=attendance.count()
    percentage=(perc/90)*100
    percentage=int(percentage)
    print(attendance)
    return render(request,'studattendance.html',{'data':attendance,'percentage':percentage})

def complaint(request):
    stud_id = request.session.get('stud_id')
    login_id = get_object_or_404(Studentreg, login_id=stud_id) 
    print(login_id)

    if request.method == 'POST':
        form=ComplaintForm(request.POST)
        a=form.save(commit=False)
        a.stud_id=login_id
        a.save()
        return redirect('user')
    else:
        form=ComplaintForm()
    return render(request,'complaint.html',{'form':form})
    
def complaintview(request):
    stud_id = request.session.get('stud_id')
    login_id = get_object_or_404(Studentreg, id=stud_id) 

    results =complaints.objects.filter(stud_id=login_id)
    return render(request,'complaintview.html',{'data':results})

def complaintdelete(request,id):
    b=get_object_or_404(complaints,id=id)
    b.delete()
    return redirect('complaintview')
def complaintedit(request,id):
    stud_id = request.session.get('stud_id')
    login_id = get_object_or_404(Studentreg, login_id=stud_id) 
    edit = get_object_or_404(complaints,id=id)
    if request.method == 'POST':
        form=ComplaintForm(request.POST,instance=edit)
        if form.is_valid():
            form.save()
            return redirect('complaintview')
    else:
        form=ComplaintForm(instance=edit)
    return render(request,'complaint.html',{'form':form}) 
    
def admincompliaintview(request):
    data=complaints.objects.all().select_related('stud_id')
    return render(request,'admincomplaint.html',{'data':data}) 

def adminreplay(request, id):
    cmp = get_object_or_404(complaints, id=id)

    if request.method == 'POST':
        form = ReplayForm(request.POST)

        if form.is_valid():
            cmp.replay = form.cleaned_data['replay']
            cmp.save()
            return redirect('admincompliaintview')  
    else:
        form = ReplayForm(initial={'replay': cmp.replay})

    return render(request, 'replayadmin.html', {'form': form, 'cmp': cmp})

from django.shortcuts import render
from .models import SubjectDetail
from django.db.models import Q

def subjects_by_semester(request):
    query = request.GET.get('q', '').strip()

    # Filter subject details based on subject's semester or department
    if query:
        subject_details = SubjectDetail.objects.filter(
            Q(subject__sem__icontains=query) |
            Q(subject__dept__icontains=query)
        ).select_related('subject')
    else:
        subject_details = SubjectDetail.objects.select_related('subject').all()

    # Grouping subject details by semester
    details_by_semester = {}
    for detail in subject_details:
        sem = detail.subject.sem
        if sem not in details_by_semester:
            details_by_semester[sem] = []
        details_by_semester[sem].append(detail)

    return render(request, 'adminsubject.html', {
        'details_by_semester': details_by_semester,
        'query': query,
    })

def asubedit(request):
    stud_id=request.session.get('stud_id')   
    course=get_object_or_404(Course,id=stud_id)
    elective=get_object_or_404(ElectiveCourse,id=stud_id)
    if request.method=='POST':
        form=CourseForm(request.POST,instance=course)
        form2=ElectiveCourseForm(request.POST, instance=elective)
        if form.is_valid() and form2.is_valid():
            form.save()
            form2.save()
            return redirect('admin')
    else:
        form=CourseForm(instance=course)
        form2= ElectiveCourseForm( instance=elective)

    return render(request, 'asubedit.html',{'form':form,'form2':form2})
def asubdel(request,id):
    a=get_object_or_404(Course,id=id)
    b=get_object_or_404(ElectiveCourse,id=id)
    a.delete()
    b.delete()

    return redirect('adminview')





# def asubjectviews(request, id):
#     student = get_object_or_404(Studentreg, id=id)

#     # Get SubjectDetail for student's department & semester
#     subject_detail = SubjectDetail.objects.filter(
#         subject__dept__iexact=student.department,
#         subject__sem=student.semester
#     ).first()

#     # Extract core subjects
#     core_subjects = []
#     if subject_detail:
#         for field in ['major1', 'major2', 'major3']:
#             value = getattr(subject_detail, field)
#             if value:
#                 core_subjects.extend([s.strip() for s in value.split(',') if s.strip()])

#     # Get student’s elective selections
#     selection = StudentSubjectSelection.objects.filter(
#         student=student,
#         subject=subject_detail  # Since we already have the SubjectDetail
#     ).first()

#     selected_subjects = []
#     if selection:
#         fields_to_check = [
#             'minorsone', 'minortwo', 'aeca', 'aecb', 'mdc',
#             'vac1', 'vac2', 'sec', 'elective1', 'elective2'
#         ]

#         field_labels = {
#             'minorsone': 'Minor 1',
#             'minortwo': 'Minor 2',
#             'aeca': 'AECC A',
#             'aecb': 'AECC B',
#             'mdc': 'MDC',
#             'vac1': 'VAC 1',
#             'vac2': 'VAC 2',
#             'sec': 'SEC',
#             'elective1': 'Elective 1',
#             'elective2': 'Elective 2',
#         }

#         for field in fields_to_check:
#             value = getattr(selection, field)
#             if value:
#                 selected_subjects.append((field_labels.get(field, field), value.strip()))

#     return render(request, 'asubjectviews.html', {
#         'student': student,
#         'core_subjects': core_subjects,
#         'selected_subjects': selected_subjects
#     })



def asubjectviews(request, id):
    student = get_object_or_404(Studentreg, login_id=id)

    selection = StudentSubjectSelection.objects.filter(student=student).first()

    core_subjects = []
    selected_subjects = []

    if selection:
        subject_detail = selection.subject

        if subject_detail:
            # Collect core subjects (major1, major2, major3)
            for field in [subject_detail.major1, subject_detail.major2, subject_detail.major3]:
                if field:
                    core_subjects += [sub.strip() for sub in field.split(',') if sub.strip()]

        # Now collect only filled selected subjects
        subject_fields = [
            ('Minor 1', selection.minorsone),
            ('Minor 2', selection.minortwo),
            ('AECA', selection.aeca),
            ('AECB', selection.aecb),
            ('MDC', selection.mdc),
            ('VAC 1', selection.vac1),
            ('VAC 2', selection.vac2),
            ('SEC', selection.sec),
            ('Elective 1', selection.elective1),
            ('Elective 2', selection.elective2),
        ]

        # Filter only the non-empty ones
        selected_subjects = [(label, val) for label, val in subject_fields if val]

    context = {
        'student': student,
        'core_subjects': core_subjects,
        'selected_subjects': selected_subjects,
    }

    return render(request, 'asubjectviews.html', context)







def removecomplaint(request,id):
    a=get_object_or_404(complaints,id=id)
    a.delete()
    return redirect('admincompliaintview')

def searchstudad(request):
    results = Login.objects.filter(usertype=1).select_related('student_as_loginid') 

    query = request.GET.get('q', '') 

    if query:
        results = results.filter(
           Q(student_as_loginid__admno__icontains=query)|
           Q(student_as_loginid__name__icontains=query)|
           Q(student_as_loginid__semester__icontains=query)|
           Q(student_as_loginid__department__icontains=query) 
    
        )

    return render(request, 'adminstudview.html', {'results': results, 'query': query})

def adminexam(request):
    if request.method == 'POST':
        form = Examdate(request.POST)
        if form.is_valid():
            form.save()
            return redirect('admin') 
    else:
        form = Examdate()
    return render(request,'adminexam.html',{'form':form})

def studexamview(request):
    results =exam.objects.all()
    return render(request,'user.html',{'data':results})

def notifications(request):
    stud_id = request.session.get('stud_id')
    login_id = get_object_or_404(Studentreg, id=stud_id) 

    results =exam.objects.all()
    return render(request,'notifications.html',{'data':results})
def notificationt(request):
    te_id = request.session.get('t_id')
    login_id = get_object_or_404(Studentreg, id=te_id) 

    results =exam.objects.all()
    return render(request,'notificationt.html',{'data':results})

import fitz  # PyMuPDF for extracting text

def get_grade(plagiarism_percentage):
    """Assigns a grade based on plagiarism percentage."""
    if plagiarism_percentage <= 10:
        return "A (Excellent)"
    elif plagiarism_percentage <= 30:
        return "B (Good)"
    elif plagiarism_percentage <= 50:
        return "C (Average)"
    elif plagiarism_percentage <= 70:
        return "D (Poor)"
    else:
        return "F (Fail)"


def extract_text_from_pdf(pdf_file):
    """Extracts text from a PDF file."""
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    text = "\n".join(page.get_text("text") for page in doc)
    return text

def extract_handwriting_with_gemini(media_file):
    """Extracts handwritten text from an image or PDF using Google Gemini Vision."""
    try:
        # Read the file content
        file_content = media_file.read()
        media_file.seek(0) # Reset pointer
        
        file_extension = os.path.splitext(media_file.name)[1].lower()
        prompt = "Transcribe the handwritten text in this document exactly as it is written. Do not add any extra commentary or formatting."
        
        if file_extension in ['.jpg', '.jpeg', '.png']:
            # Handle standard images
            image = Image.open(media_file)
            response = client.models.generate_content(
                model='gemini-flash-latest',
                contents=[prompt, image]
            )
            return response.text
            
        elif file_extension == '.pdf':
            # Handle PDF by uploading it using the File API
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_pdf:
                temp_pdf.write(file_content)
                temp_pdf_path = temp_pdf.name
                
            try:
                uploaded_file = client.files.upload(path=temp_pdf_path)
                response = client.models.generate_content(
                    model='gemini-flash-latest',
                    contents=[prompt, uploaded_file]
                )
                return response.text
            finally:
                os.remove(temp_pdf_path)
                
        else:
            return "Unsupported file format for handwriting recognition."
            
    except Exception as e:
        print(f"Error extracting handwriting with Gemini: {e}")
        return f"Error during handwriting extraction: {str(e)}"

import requests

SERPAPI_KEY = "7c8d23c1d5c1cdbab8a8517a0bde42da6cefda61c0af21bdeebf362d403cfa29"  # Replace with your SerpAPI key

def search_serpapi(query):
    """Searches Google Scholar using SerpAPI."""
    url = "https://serpapi.com/search"
    params = {
        "api_key": SERPAPI_KEY,
         "q": f'"{query}"',
        "engine": "google_scholar",
        "num": 5  # Number of results
    }

    try:
        response = requests.get(url, params=params)
        data = response.json()

        if "organic_results" in data:
            return [result["link"] for result in data["organic_results"]]
    except Exception as e:
        print(f"Error: {e}")

    return []


def check_plagiarism(text):
    """Checks plagiarism and calculates plagiarism percentage."""
    sentences = text.split(". ")[:10]  # Check first 10 sentences
    total_sentences = len(sentences)
    matched_sentences = 0
    plagiarism_results = {}

    for sentence in sentences:
        search_results = search_serpapi(sentence)  # Exact match search
        if search_results:
            matched_sentences += 1
            plagiarism_results[sentence] = search_results

    # Calculate plagiarism percentage
    plagiarism_percentage = (matched_sentences / total_sentences) * 100 if total_sentences > 0 else 0

    return plagiarism_results, plagiarism_percentage


def essaycheck(request, id):
    log_id = request.session.get('t_id')
    essay_id = get_object_or_404(Essay,id = id)
    tc_id = get_object_or_404(teacherreg, login_id=log_id)
    essay = Essay.objects.filter(tea_id=tc_id).last()


    plagiarism_results = None
    plagiarism_percentage = 0
    grade = "N/A"
    extracted_text = ""
    # essay = Essay.objects.get(pk=essay_id)


    if request.method == 'POST':
        form = Essayup(request.POST, request.FILES)
        if form.is_valid():
            pdf_file = request.FILES['essay']
            
            # Use Gemini for extraction (handles both Image and PDF)
            extracted_text = extract_handwriting_with_gemini(pdf_file)
            
            # Fallback to standard PDF extraction if Gemini fails or returns empty
            if not extracted_text or "Error" in extracted_text or "Unsupported" in extracted_text:
                pdf_file.seek(0) # Reset pointer before reading again
                try:
                    extracted_text = extract_text_from_pdf(pdf_file)
                except Exception as e:
                    print(f"Fallback PDF extraction failed: {e}")
                    extracted_text = extracted_text if extracted_text else "Could not extract text."

            # Check plagiarism and get percentage
            plagiarism_results, plagiarism_percentage = check_plagiarism(extracted_text)

            # Assign a grade
            grade = get_grade(plagiarism_percentage)

    else:
        form = Essayup()
        # essay = Essay.objects.filter(tea_id=tc_id).last() 
    return render(request, 'essaycheck.html', {
        'form': form,
        'essay': essay,
        'plagiarism_results': plagiarism_results,
        'plagiarism_percentage': plagiarism_percentage,
        'grade': grade,
        'extracted_text': extracted_text[:500],  # Show first 500 chars
        # 'essay': essay

    })

def save_essay_marks(request,essay_id):
    # print(essay_id)
    if request.method == 'POST':
        essay = get_object_or_404(Essay, pk=essay_id)
        mark = request.POST.get('mark')
        grade = request.POST.get('grade')
        # print(essay)

        # Assuming your Essay model has fields for mark and grade
        essay.mark = mark
        essay.grade = grade
        essay.save()

        return redirect('viewessayt')

    return redirect('essaycheck')  # or some error page

def subject_selection_view(request):
    st = request.session.get('stud_id')
    student = get_object_or_404(Studentreg, login_id=st)

    # Check if student has already submitted a selection
    if StudentSubjectSelection.objects.filter(student=student).exists():
        messages.info(request, "You have already submitted your subject selections.")
        return redirect('user')  # Adjust the redirect page as needed

    # Get subject & details based on student's semester and department
    subject = Subject.objects.filter(dept=student.department, sem=student.semester).first()
    subject_detail = SubjectDetail.objects.filter(subject=subject).first()

    if request.method == 'POST':
        form = StudentSelectionForm(request.POST, subject_detail=subject_detail, student=student)
        if form.is_valid():
            selection = form.save(commit=False)
            selection.student = student
            selection.subject = subject_detail  # or subject_detail if you want to track the details
            selection.save()
            return redirect('user')  # Redirect to the appropriate page
    else:
        form = StudentSelectionForm(subject_detail=subject_detail, student=student)

    context = {
        'form': form,
        'subject': subject,
        'subject_detail': subject_detail,
    }
    return render(request, 's.html', context)


def subjectstudview(request):
    student_id = request.session.get('stud_id')
    st = get_object_or_404(Studentreg, login_id=student_id)

    # Student's selected subjects
    selection = StudentSubjectSelection.objects.filter(student=st).first()
    subject_detail = selection.subject if selection else None

    # Core subjects
    core_subjects = []
    if subject_detail:
        for field in ['major1', 'major2', 'major3']:
            field_value = getattr(subject_detail, field, None)
            if field_value:
                core_subjects.extend([sub.strip() for sub in field_value.split(',') if sub.strip()])

    # Elective subjects
    elective_fields = ['minorsone', 'minortwo', 'aeca', 'aecb', 'mdc', 'vac1', 'vac2', 'sec', 'elective1', 'elective2']
    elective_subjects = []
    if selection:
        for field in elective_fields:
            val = getattr(selection, field, None)
            if val:
                elective_subjects.append(val.strip())

    # Get marks from InternalMarks model
    marks_queryset = InternalMarks.objects.filter(stud_id=st)
    marks_dict = {mark.subject.strip().lower(): mark.marks for mark in marks_queryset}

    # Pair subjects with marks
    core_subjects_with_marks = [(subj, marks_dict.get(subj.lower(), 'Not Available')) for subj in core_subjects]
    elective_subjects_with_marks = [(subj, marks_dict.get(subj.lower(), 'Not Available')) for subj in elective_subjects]

    return render(request, 'viewsubject.html', {
        'student': st,
        'core_subjects_with_marks': core_subjects_with_marks,
        'elective_subjects_with_marks': elective_subjects_with_marks,
    })


def internals_elective(request, student_id, subject_name):
    # electives = get_object_or_404(StudentSubjectSelection, id=subject_name)
    electives = SubjectDetail.objects.filter(
    Q(minorsone__icontains=subject_name) |
    Q(minortwo__icontains=subject_name) |
    Q(aeca__icontains=subject_name) |
    Q(aecb__icontains=subject_name) |
    Q(mdc__icontains=subject_name) |
    Q(vac1__icontains=subject_name) |
    Q(vac2__icontains=subject_name) |
    Q(sec__icontains=subject_name) |
    Q(elective1__icontains=subject_name) |
    Q(elective2__icontains=subject_name)
    ).first()
    student = get_object_or_404(Studentreg, id=student_id)
    if not electives:
        return HttpResponseNotFound("Subject not found.")

    logid = request.session.get('t_id')
    teacher = get_object_or_404(teacherreg, login_id=logid)

    if request.method == 'POST':
        marks = request.POST.get('marks')
        if not marks.isdigit():
            messages.error(request, "Marks must be numeric.")
        elif InternalMarks.objects.filter(subject=subject_name, stud_id=student).exists():
            messages.error(request, 'Marks already exist for this subject.')
        else:
            InternalMarks.objects.create(
                subject=subject_name,
                stud_id=student,
                marks=int(marks),
                login_id=teacher
            )
            messages.success(request, 'Marks uploaded successfully!')
            return redirect('viewsubjectt', id=student.id)


    return render(request, 'uploadmark_teacher.html', {
        'electives': electives,
        'student': student
    })




def internals_major(request, student_id, subject_name):
    student = get_object_or_404(Studentreg, id=student_id)

    # Try to find SubjectDetail where any of the major fields match subject_name
    subject_detail = SubjectDetail.objects.filter(
        Q(major1__icontains=subject_name) |
        Q(major2__icontains=subject_name) |
        Q(major3__icontains=subject_name)
    ).first()

    if not subject_detail:
        return HttpResponseNotFound("Subject not found.")

    logid = request.session.get('t_id')
    teacher = get_object_or_404(teacherreg, login_id=logid)

    if request.method == 'POST':
        marks = request.POST.get('marks')
        if not marks.isdigit():
            messages.error(request, "Marks must be numeric.")
        elif InternalMarks.objects.filter(subject=subject_name, stud_id=student).exists():
            messages.error(request, 'Marks already exist for this subject.')
        else:
            InternalMarks.objects.create(
                subject=subject_name,
                stud_id=student,
                marks=int(marks),
                login_id=teacher
            )
            messages.success(request, 'Marks uploaded successfully!')
            return redirect('viewsubjectt', id=student.id)

    return render(request, 'uploadmark_teacher_major.html', {
        'core': subject_detail,
        'subject_name': subject_name,
        'student': student
    })

from django.db.models import Q
from .models import InternalMarks, SubjectDetail, Studentreg, teacherreg, StudentSubjectSelection

def teacher_view_marks(request):
    teacher_id = request.session.get('t_id')
    if not teacher_id:
        return HttpResponse("Teacher not logged in or session expired", status=401)

    teacher = get_object_or_404(teacherreg, login_id=teacher_id)

    marks_uploaded = InternalMarks.objects.filter(login_id=teacher)

    if 'dept' in request.GET and request.GET['dept']:
        marks_uploaded = marks_uploaded.filter(stud_id__department=request.GET['dept'])

    if 'sem' in request.GET and request.GET['sem']:
        marks_uploaded = marks_uploaded.filter(stud_id__semester=request.GET['sem'])

    if 'subject' in request.GET and request.GET['subject']:
        marks_uploaded = marks_uploaded.filter(subject=request.GET['subject'])

    return render(request, 'markviewtech.html', {
        'marks_uploaded': marks_uploaded,
        'teacher': teacher,
    })

def is_hod(teacher):
    return teacher.is_hod  # Make sure `is_hod` field is defined in `teacherreg` model


def add_subject_detail(request):
    teacher_id = request.session.get('t_id')
    if not teacher_id:
        return redirect('login')  # If not logged in

    teacher = get_object_or_404(teacherreg, login_id=teacher_id)

    # ✅ Only HOD can access this page
    if not is_hod(teacher):
        messages.error(request, "Access denied. Only HODs can upload subjects.")
        return redirect('tuser')  # Or wherever teachers go by default

    if request.method == 'POST':
        form = SubjectaddForm(request.POST)
        if form.is_valid():
            subject_instance = form.save(commit=False)
            subject_instance.hod = teacher  # 👈 Assign HOD here
            subject_instance.save()
            messages.success(request, "Subject details uploaded successfully.")
            return redirect('adddepsub')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = SubjectaddForm()

    return render(request, 'adddepsub.html', {'form': form})
def view_subjects_by_dept_and_hod(request):
    teacher_id = request.session.get('t_id')
    if not teacher_id:
        return redirect('login')

    hod = get_object_or_404(teacherreg, login_id=teacher_id)

    semester = request.GET.get('tsemester')  # Get from URL: ?semester=Sem 1
    subjects = Subjectadd.objects.filter(hod=hod, subject__dept=hod.tdepartment)

    if semester:
        subjects = subjects.filter(subject__sem=semester)

    return render(request, 'viewsub.html', {
        'subjects': subjects,
        'dept': hod.tdepartment,
        'semester': semester
    })
def view_subjects_by_hod(request):
    teacher_id = request.session.get('t_id')
    if not teacher_id:
        return redirect('login')  # redirect if not logged in

    hod = get_object_or_404(teacherreg, login_id=teacher_id)
    semester = request.GET.get('semester')  # e.g., ?semester=Sem 1

    # Base filter: only this HOD's department subjects
    subjects = Subjectadd.objects.filter(
        hod=hod,
        subject__dept=hod.tdepartment
    )

    # Optional filter by semester
    if semester:
        subjects = subjects.filter(subject__sem=semester)

    return render(request, 'viewsub.html', {
        'subjects': subjects,
        'dept': hod.tdepartment,
        'semester': semester
    })

def admindepartment(request):
    teacher_id = request.session.get('t_id')
    if not teacher_id:
        return redirect('login')  # User not logged in

    # Get the HOD (teacher) object
    hod = get_object_or_404(teacherreg, login_id=teacher_id)

    # Get semester from request parameters (e.g., ?tsemester=Sem 1)
    semester = request.GET.get('tsemester')

    # Fetch subjects for this HOD
    subjects = Subjectadd.objects.filter(hod=hod)

    # Optional: filter by semester if provided
    if semester:
        subjects = subjects.filter(subject__sem=semester)

    # Pass the data to the template
    context = {
        'subjects': subjects,
        'dept': hod.tdepartment,
        'semester': semester,
    }

    return render(request, 'admindepartment.html', context)


def extract_questions_from_pdf(pdf_path):
    reader = PdfReader(pdf_path)
    return ''.join(page.extract_text() for page in reader.pages)

def parse_mcqs(text):
    pattern = r"(\d+)\.\s*(.*?)\nA\.\s*(.*?)\nB\.\s*(.*?)\nC\.\s*(.*?)\nD\.\s*(.*?)\n"
    matches = re.findall(pattern, text, re.DOTALL)
    return [{
        'question': m[1].strip(),
        'A': m[2].strip(),
        'B': m[3].strip(),
        'C': m[4].strip(),
        'D': m[5].strip(),
    } for m in matches]

def infer_correct_answers_nemotron(questions):
    endpoint = "https://integrate.api.nvidia.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {NVIDIA_API_KEY}",
        "Content-Type": "application/json"
    }
    predicted = {}
    for i, q in enumerate(questions):
        prompt = (
            f"Question: {q['question']}\n"
            f"A. {q['A']}\nB. {q['B']}\nC. {q['C']}\nD. {q['D']}\n"
            f"Choose the correct option (A, B, C, or D) only:"
        )
        payload = {
            "model": "nvidia/llama-3.1-nemotron-70b-instruct",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
            "max_tokens": 10
        }
        try:
            response = requests.post(endpoint, headers=headers, json=payload)
            result = response.json()
            ans = result['choices'][0]['message']['content'].strip()
            predicted[i] = next((c for c in ans if c in CHOICES), '?')
        except Exception as e:
            print(f"API error for Q{i+1}: {e}")
            predicted[i] = '?'
    return predicted

def extract_student_answers(img_path):
    image = cv2.imread(img_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = cv2.Canny(blurred, 75, 200)

    cnts, _ = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    question_cnts = [c for c in cnts if 15 <= cv2.boundingRect(c)[2] <= 60 and
                     15 <= cv2.boundingRect(c)[3] <= 60 and
                     0.8 <= cv2.boundingRect(c)[2] / float(cv2.boundingRect(c)[3]) <= 1.2]

    question_cnts = sorted(question_cnts, key=lambda c: cv2.boundingRect(c)[1])
    student_answers = {}

    for i in range(0, len(question_cnts) // 4):
        row = sorted(question_cnts[i*4:(i+1)*4], key=lambda c: cv2.boundingRect(c)[0])
        filled, max_val = None, 0
        for idx, cnt in enumerate(row):
            mask = np.zeros(gray.shape, dtype="uint8")
            cv2.drawContours(mask, [cnt], -1, 255, -1)
            total = cv2.countNonZero(cv2.bitwise_and(gray, gray, mask=mask))
            if total > max_val:
                max_val, filled = total, idx
        if filled is not None:
            student_answers[i] = CHOICES[filled]
    return student_answers

def uploadtechs(request, id):
    stud_id = request.session.get('stud_id')   
    login_details = get_object_or_404(Login, id=stud_id)
    tc_id = get_object_or_404(teacherreg, id=id)
    print('hiii')
    if request.method == 'POST':
        form = omrform(request.POST, request.FILES)
        print(form)
        if form.is_valid():
            a = form.save(commit=False)
            a.login_id = login_details
            a.tc_id = tc_id
            a.save()
            return redirect('user')
    else:
        form = omrform()

    return render(request, 'uploadtechs.html', {'form': form})

def uploadomr(request, id):
    stud_id = request.session.get('t_id')
    login_details = get_object_or_404(Login, id=stud_id)
    tc_id = get_object_or_404(teacherreg, login_id=login_details)

    score, ai_answers, student_answers = 0, {}, {}

    if request.method == 'POST':
        form = omr(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.login_id = login_details
            obj.tc_id = tc_id
            obj.save()

            qfile = request.FILES['question_paper']
            omrfile = request.FILES['omr']
            qpath = default_storage.save('temp/questions.pdf', qfile)
            opath = default_storage.save('temp/omr.jpg', omrfile)

            text = extract_questions_from_pdf(default_storage.path(qpath))
            parsed_questions = parse_mcqs(text)
            ai_answers = infer_correct_answers_nemotron(parsed_questions)
            student_answers = extract_student_answers(default_storage.path(opath))

            for i, s_ans in student_answers.items():
                if ai_answers.get(i) == s_ans:
                    score += 1
    else:
        form = omr()

    return render(request, 'uploadomr.html', {
        'form': form,
        'score': score,
        'ai_answers': ai_answers,
        'student_answers': student_answers
    })


def extract_questions_and_marks_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    # Example pattern: 1. What is 2+2? (5 marks)
    pattern = r"\d+\.\s*(.*?)\s*\((\d+)\s*marks?\)"
    matches = re.findall(pattern, text, re.DOTALL)
    questions = [{'question': q.strip(), 'marks': int(m)} for q, m in matches]
    return questions

def evaluate_with_ai(question, student_answer):
    endpoint = "https://integrate.api.nvidia.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {NVIDIA_API_KEY}",
        "Content-Type": "application/json"
    }
    prompt = (
        f"Evaluate the student's answer.\n"
        f"Question: {question}\n"
        f"Student's Answer: {student_answer}\n"
        f"Provide marks out of 10 and justification."
    )
    payload = {
        "model": "nvidia/llama-3.1-nemotron-70b-instruct",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "max_tokens": 100
    }
    response = requests.post(endpoint, headers=headers, data=json.dumps(payload))
    if response.status_code == 200:
        content = response.json()['choices'][0]['message']['content']
        match = re.search(r'(\d+)/10', content)
        marks = int(match.group(1)) if match else 0
        return marks, content
    return 0, "AI response failed."

def extract_student_answers_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    # Assuming answer format: 1. answer text
    pattern = r"\d+\.\s*(.*?)(?=\d+\.|$)"
    answers = re.findall(pattern, text, re.DOTALL)
    return [ans.strip() for ans in answers]

def evaluate_answers(request, answer_id):
    if request.method == 'POST':
        teacher_id = request.session.get('t_id')
        teacher = get_object_or_404(teacherreg, login_id=teacher_id)
        answer_obj = get_object_or_404(Answer, id=answer_id)

        # Save uploaded question paper
        question_paper = request.FILES.get('question_paper')
        if not question_paper:
            return render(request, 'error.html', {'message': 'No question paper uploaded.'})

        question_path = default_storage.save('temp/questions.pdf', question_paper)
        question_full_path = default_storage.path(question_path)

        questions = extract_questions_and_marks_from_pdf(question_full_path)
        student_answer_path = default_storage.path(answer_obj.answer.name)
        student_answers = extract_student_answers_from_pdf(student_answer_path)

        total_score = 0
        evaluations = []

        for i, q in enumerate(questions):
            student_ans = student_answers[i] if i < len(student_answers) else ""
            score, feedback = evaluate_with_ai(q['question'], student_ans)
            max_marks = q['marks']
            actual_score = min(score, max_marks)  # Clamp to question's max mark

            evaluations.append({
                'question': q['question'],
                'student_answer': student_ans,
                'score': actual_score,
                'max': max_marks,
                'feedback': feedback
            })
            total_score += actual_score

        # Save result
        EvaluationResult.objects.create(
            student=answer_obj.login_id,
            teacher=teacher,
            answer=answer_obj,
            total_score=total_score,
            details=json.dumps(evaluations)
        )

        return render(request, 'evaluation_result.html', {
            'student': answer_obj.login_id.student_as_loginid,
            'evaluations': evaluations,
            'total_score': total_score
        })

    return redirect('tuser')

# def teacher_essays(request, id):
#     teacher = get_object_or_404(teacherreg, id=id)
#     essays = Essay.objects.filter(tea_id=teacher)

#     return render(request, 'teacher_essays.html', {
#         'teacher': teacher,
#         'essays': essays
#     })