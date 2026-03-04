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
import threading
import time
# Configure Gemini API Key
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
NVIDIA_API_KEY = "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"
CHOICES = ['A', 'B', 'C', 'D']

# ---- Self-Ping to avoid Render inactivity ----
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL", "")

def _self_ping_worker():
    """Pings the app every 10 minutes to prevent Render from sleeping."""
    time.sleep(30)  # Give server time to start
    while True:
        try:
            if RENDER_URL:
                requests.get(f"{RENDER_URL}/ping", timeout=10)
                print("[Self-Ping] Pinged successfully")
        except Exception as e:
            print(f"[Self-Ping] Error: {e}")
        time.sleep(600)  # Every 10 minutes

# Start ping thread only once (not during management commands)
if os.environ.get("RUN_MAIN") != "true" or os.environ.get("RENDER_EXTERNAL_URL"):
    _ping_thread = threading.Thread(target=_self_ping_worker, daemon=True)
    _ping_thread.start()

def ping(request):
    """Simple health-check endpoint."""
    return HttpResponse("pong", content_type="text/plain", status=200)

def main(request):
    teachers = teacherreg.objects.filter(login_id__status='1')
    return render(request, 'main.html', {'teachers': teachers})
def admin(request):
    user_count = Studentreg.objects.all().count()
    t_count = teacherreg.objects.all().count()
    return render(request, 'admin.html',{'user_count': user_count,'t_count':t_count})
def user(request):
    from datetime import date, timedelta
    stud_id = request.session.get('stud_id')
    results = exam.objects.all().order_by('date')
    teachers = teacherreg.objects.filter(login_id__status='1')
    today = date.today()
    notification_count = results.count()
    upcoming_alert = results.filter(date__lte=today + timedelta(days=2), date__gte=today)
    return render(request, 'user.html', {
        'data': results,
        'teachers': teachers,
        'notification_count': notification_count,
        'upcoming_alert': upcoming_alert,
    })
def tuser(request):
    teachers = teacherreg.objects.filter(login_id__status='1')
    return render(request, 'tuser.html', {'teachers': teachers})
def studentreg(request):
    if request.method == 'POST':
        form=studentform(request.POST,request.FILES)
        logins=loginform(request.POST)
        print(form)
        if form.is_valid() and logins.is_valid():
            b=form.save(commit=False)
            a=logins.save(commit=False)
            a.usertype=1
            a.status=1 # Approve student by default
            # Auto-generate username from admno or email for students
            if not a.username:
                if b.admno:
                    a.username = b.admno
                elif a.email:
                    a.username = a.email
                else:
                    import uuid
                    a.username = f"std_{uuid.uuid4().hex[:6]}"
            a.save()
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
    return render(request,'adminstudview.html',{'results':view_id})
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
            # Auto-generate username from Email for teachers
            if not a.username and a.email:
                a.username = a.email
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
            username_input = form.cleaned_data['username']
            password = form.cleaned_data['password'].strip()
            print(f"DEBUG: Attempting login for identifier: {username_input}")
            try:
                # Check both username and email fields
                user = Login.objects.filter(
                    Q(username=username_input) | Q(email=username_input)
                ).first()
                
                if not user:
                    print("DEBUG: User does not exist")
                    messages.error(request, 'User does not exist')
                    return redirect('login')

                print(f"DEBUG: User found: {user.username}, usertype: {user.usertype}, status: {user.status}")
                
                if user.password.strip() == password:
                    print("DEBUG: Password matched")
                    # Check status for students and teachers
                    if user.usertype in [1, 2]:
                        if user.status == 2:
                            messages.error(request, 'Your account has been rejected.')
                            return redirect('login')
                        elif user.status == 0:
                            messages.error(request, 'Your account is under review.')
                            return redirect('login')

                    # Success - Set session and redirect
                    if user.usertype == 1:
                        request.session['stud_id'] = user.id
                        return redirect('user')
                    elif user.usertype == 2:
                        request.session['t_id'] = user.id
                        return redirect('tuser')
                    elif user.usertype == 3:
                        request.session['a_id'] = user.id
                        return redirect('admin')
                else:
                    messages.error(request, 'Invalid password')
            except Exception as e:
                print(f"DEBUG: Login error: {e}")
                messages.error(request, 'An error occurred during login.')
    else:
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
            uploaded_file = request.FILES.get('essay')
            if uploaded_file:
                a=form.save(commit=False)
                a.login_id=login_details
                a.student = stud
                a.tea_id=te_id
                a.transcription = "Processing in background..."
                a.rating = "Pending..."
                a.save()
                
                # Start background thread for processing essay
                def process_essay_in_background(essay_id):
                    import io, requests, time
                    try:
                        time.sleep(2)
                        from .models import Essay
                        essay_obj = Essay.objects.get(id=essay_id)
                        res = requests.get(essay_obj.essay.url)
                        res.raise_for_status()
                        
                        file_bytes = io.BytesIO(res.content)
                        file_bytes.name = essay_obj.essay.name.split('/')[-1] if essay_obj.essay.name else "essay.pdf"
                        
                        transcription = extract_handwriting_with_gemini(file_bytes)
                        rating = rate_essay_with_ai(transcription)
                        
                        essay_obj.transcription = transcription
                        essay_obj.rating = rating
                        essay_obj.save(update_fields=['transcription', 'rating'])
                    except Exception as e:
                        print(f"Background essay processing failed: {e}")
                        try:
                            from .models import Essay
                            essay_obj = Essay.objects.get(id=essay_id)
                            essay_obj.rating = "Error processing essay files."
                            essay_obj.save(update_fields=['rating'])
                        except:
                            pass

                import threading
                threading.Thread(target=process_essay_in_background, args=(a.id,)).start()
                return redirect('viewessay')
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
        uploaded_file = request.FILES.get('assignment')
        if uploaded_file:
            a = Assignment(
                assignment=uploaded_file,
                login_id=student_obj,
                ta_id=tc_id,
                question=question_obj
            )
            a.transcription = "Processing in background..."
            a.rating = "Pending..."
            a.save()
            
            # Start background thread for processing
            def process_in_background(assignment_id):
                import io, requests
                try:
                    # Let the database commit and Cloudinary finish its initial sync
                    time.sleep(2)
                    from .models import Assignment
                    assign_obj = Assignment.objects.get(id=assignment_id)
                    res = requests.get(assign_obj.assignment.url)
                    res.raise_for_status()
                    
                    file_bytes = io.BytesIO(res.content)
                    file_bytes.name = assign_obj.assignment.name.split('/')[-1] if assign_obj.assignment.name else "submission.pdf"
                    
                    transcription = extract_handwriting_with_gemini(file_bytes)
                    rating = rate_assignment_with_ai(transcription, assign_obj.question.question_text)
                    
                    assign_obj.transcription = transcription
                    assign_obj.rating = rating
                    assign_obj.save()
                except Exception as e:
                    try:
                        from .models import Assignment
                        assign_obj = Assignment.objects.get(id=assignment_id)
                        assign_obj.transcription = "Failed to process."
                        assign_obj.rating = f"Error: {str(e)}"
                        assign_obj.save()
                    except:
                        pass
            
            thread = threading.Thread(target=process_in_background, args=(a.id,))
            thread.daemon = True
            thread.start()
            
            messages.success(request, f"Assignment '{question_obj.title}' uploaded successfully. Waiting for AI review...")
            return redirect('viewassignment')
        else:
            messages.error(request, "Please attach a file.")
    else:
        form=assignment()
    return render(request, 'uploadassignment.html',{'form':form, 'question': question_obj})

def add_assignment_view(request):
    tea_id = request.session.get('t_id')
    teacher = get_object_or_404(teacherreg, login_id=tea_id)
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        question_text = request.POST.get('question_text', '').strip()
        if title and question_text:
            aq = AssignmentQuestion.objects.create(
                teacher=teacher,
                title=title,
                question_text=question_text
            )
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'assignment': {
                        'id': aq.id,
                        'title': aq.title,
                        'question_text': aq.question_text,
                        'created_at': aq.created_at.strftime('%b %d, %Y'),
                    }
                })
            messages.success(request, "Assignment created successfully.")
            return redirect('viewassignmentt')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'Title and question are required.'})
            messages.error(request, "Title and question are required.")
    
    # GET: render combined view+add page
    assignments = AssignmentQuestion.objects.filter(teacher=teacher).order_by('-created_at')
    all_submissions = Assignment.objects.filter(ta_id=teacher).select_related('login_id', 'question')
    return render(request, 'viewassignmentt.html', {
        'assignments': assignments,
        'submissions': all_submissions,
    })

def student_assignments_view(request):
    stud_id = request.session.get('stud_id')
    student_obj = get_object_or_404(Studentreg, login_id=stud_id) if stud_id else None
    assignments = AssignmentQuestion.objects.all().order_by('-created_at')
    
    submitted_ids = []
    if student_obj:
        submitted_ids = list(Assignment.objects.filter(login_id=student_obj).values_list('question_id', flat=True))
    
    return render(request, 'student_assignments.html', {'assignments': assignments, 'submitted_ids': submitted_ids})

def rate_assignment_with_ai(transcription, question_text):
    prompt = f"""
    Evaluate the following student's handwritten transcription against the assignment question for relevance and correctness.
    Provide an AI Score out of 10, a rating (Excellent, Good, Average, or Poor), and a short one-sentence feedback.
    
    Assignment Question: {question_text}
    Student Submission: {transcription}
    
    Format:
    AI Score: [X]/10
    Rating: [Rating]
    Feedback: [Feedback]
    """
    try:
        client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
        response = client.models.generate_content(
            model='gemini-flash-latest',
            contents=[prompt]
        )
        return response.text
    except Exception as e:
        print(f"Rating error: {e}")
        return "Rating unavailable"

def rate_essay_with_ai(transcription):
    prompt = f"""
    Evaluate the following student's handwritten essay for coherence, argumentation, grammar, and grammar correctness.
    Provide an AI Score out of 10, a rating (Excellent, Good, Average, or Poor), and a short one-sentence feedback.
    
    Student Essay Submission: {transcription}
    
    Format:
    AI Score: [X]/10
    Rating: [Rating]
    Feedback: [Feedback]
    """
    try:
        from google import genai
        import os
        client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
        response = client.models.generate_content(
            model='gemini-flash-latest',
            contents=[prompt]
        )
        return response.text
    except Exception as e:
        print(f"Essay Rating error: {e}")
        return "Rating unavailable"

def viewassignment(request):
    stud_id=request.session.get('stud_id')
    student_obj=get_object_or_404(Studentreg,login_id=stud_id)
    submissions = Assignment.objects.filter(login_id=student_obj).select_related('question')

    return render(request,'viewassignment.html',{'submissions':submissions})

def poll_assignment_status(request, id):
    try:
        assignment = Assignment.objects.get(id=id)
        return JsonResponse({
            'status': 'success',
            'rating': assignment.rating,
            'transcription': assignment.transcription
        })
    except Assignment.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Assignment not found.'})

def poll_essay_status(request, id):
    try:
        from .models import Essay
        essay = Essay.objects.get(id=id)
        return JsonResponse({
            'status': 'success',
            'rating': essay.rating,
            'transcription': essay.transcription
        })
    except Exception:
        return JsonResponse({'status': 'error', 'message': 'Essay not found.'})

def poll_omr_status(request, id):
    try:
        from .models import Omr
        omr_obj = Omr.objects.get(id=id)
        return JsonResponse({
            'status': 'success',
            'rating': omr_obj.rating,
            'transcription': omr_obj.transcription
        })
    except Exception:
        return JsonResponse({'status': 'error', 'message': 'OMR not found.'})

def process_omr_in_background(omr_id):
    import traceback
    try:
        from .models import Omr
        omr_obj = Omr.objects.get(id=omr_id)
        
        qpath = omr_obj.question_paper.path if omr_obj.question_paper else ""
        opath = omr_obj.omr.path if omr_obj.omr else ""
        
        if not qpath or not opath:
            omr_obj.rating = "Error: Question paper or OMR file missing."
            omr_obj.transcription = "Failed"
            omr_obj.save(update_fields=['rating', 'transcription'])
            return

        text = extract_questions_from_pdf(qpath)
        parsed_questions = parse_mcqs(text)
        ai_answers = infer_correct_answers_nemotron(parsed_questions)
        student_answers = extract_student_answers(opath)
        
        score = 0
        total_questions = len(ai_answers) if ai_answers else 0
        
        detailed_feedback = ""
        for i, s_ans in student_answers.items():
            correct = ai_answers.get(i)
            if correct == s_ans:
                score += 1
                detailed_feedback += f"Q{i}: {s_ans} (Correct)\n"
            else:
                detailed_feedback += f"Q{i}: {s_ans} (Incorrect, Expected: {correct})\n"

        rating = f"Score: {score}/{total_questions}\n\nFeedback:\n{detailed_feedback}"
        
        omr_obj.transcription = "Completed"
        omr_obj.rating = rating
        omr_obj.save(update_fields=['transcription', 'rating'])
    except Exception as e:
        print(f"OMR background processing error: {e}")
        traceback.print_exc()
        try:
            from .models import Omr
            omr_obj = Omr.objects.get(id=omr_id)
            omr_obj.rating = "Error processing OMR files."
            omr_obj.transcription = "Failed"
            omr_obj.save(update_fields=['rating', 'transcription'])
        except:
            pass


def removeassignment(request, id):
    a=get_object_or_404(Assignment, id=id)
    a.delete()
    return redirect('viewassignment')

def retry_ai_grade(request, id):
    import io
    import requests
    
    assignment = get_object_or_404(Assignment, id=id)
    if not assignment.assignment:
        messages.error(request, "No file attached to this submission.")
        return redirect('viewassignmentt')
        
    try:
        # Fetch the file fully into memory
        response = requests.get(assignment.assignment.url)
        response.raise_for_status()
        
        file_bytes = io.BytesIO(response.content)
        file_bytes.name = assignment.assignment.name.split('/')[-1] if assignment.assignment.name else "submission.pdf"
        
        transcription = extract_handwriting_with_gemini(file_bytes)
        rating = rate_assignment_with_ai(transcription, assignment.question.question_text)
        
        assignment.transcription = transcription
        assignment.rating = rating
        assignment.save()
        messages.success(request, f"AI grading retried successfully for {assignment.login_id.name}.")
        
    except Exception as e:
        messages.error(request, f"Failed to retry AI processing: {str(e)}")
        
    return redirect('viewassignmentt')

def retry_omr_ai(request, id):
    import threading
    from .models import Omr
    from django.contrib import messages
    omr_obj = get_object_or_404(Omr, id=id)
    omr_obj.rating = "Pending AI Evaluation..."
    omr_obj.transcription = "pending"
    omr_obj.save(update_fields=['rating', 'transcription'])
    threading.Thread(target=process_omr_in_background, args=(omr_obj.id,)).start()
    messages.success(request, "OMR evaluation restarted.")
    return redirect('viewomrt')

def viewassignmentt(request):
    return redirect('add_assignment')

def upload_assignment_mark(request, id):
    assignments = get_object_or_404(Assignment, id=id)

    if request.method == 'POST':
        mark = request.POST.get('mark')
        if mark:
            try:
                assignments.mark = float(mark)
                assignments.save()
                messages.success(request, f"Mark updated for {assignments.login_id.name}.")
            except ValueError:
                messages.error(request, "Invalid mark format. Please enter a number.")
        return redirect('viewassignmentt')

    return redirect('viewassignmentt')


def removeassignmentt(request,id):
    b=get_object_or_404(Assignment,id=id)
    b.delete()
    return redirect('viewassignmentt')

def viewattendance(request):
    form=attendance()
    dept = request.GET.get('department') 
    sem = request.GET.get('semester') 
    subject = request.GET.get('subject')
    results = Studentreg.objects.filter(department__iexact=dept,semester=sem) 
    
    if results:
        # Fetch today's attendance for this subject and department to highlight status
        today_attendance = Attendance.objects.filter(
            current_date=date.today(),
            subject=subject
        )
        
        # Map student IDs to their attendance record for quick lookup
        marked_map = {att.login_id_id: att for att in today_attendance}
        
        # Add status to each student object
        for student in results:
            att_record = marked_map.get(student.id)
            if att_record:
                if att_record.present == 1: student.attendance_status = 'present'
                elif att_record.absent == 2: student.attendance_status = 'absent'
            else:
                student.attendance_status = None

        return render(request, 'attendancetable.html', {
            'results': results, 
            'subject': subject
        })
    elif dept or sem:
        messages.error(request, "No students found in the selected department and semester.")
    
    return render(request, 'attendance.html',{'form':form})

def present(request,id, subject_name):
    a=get_object_or_404(Studentreg,id=id)
    tea_id = request.session.get('t_id')
    login_details = get_object_or_404(teacherreg, login_id=tea_id)
    # Delete any existing record for this student and subject today to overwrite
    Attendance.objects.filter(login_id=a, subject=subject_name, current_date=date.today()).delete()
    
    Attendance.objects.create(t_id= login_details,login_id=a,present=1, subject=subject_name)
    return JsonResponse({'status': 'success', 'message': f'Attendance marked for {subject_name}!'})


def absent(request,id, subject_name):
    a=get_object_or_404(Studentreg,id=id)
    tea_id = request.session.get('t_id')
    login_details = get_object_or_404(teacherreg, login_id=tea_id)
    # Delete any existing record for this student and subject today to overwrite
    Attendance.objects.filter(login_id=a, subject=subject_name, current_date=date.today()).delete()
    
    Attendance.objects.create(t_id= login_details,login_id=a,absent=2, subject=subject_name)
    return JsonResponse({'status': 'success', 'message': f'Attendance marked for {subject_name}!'})

def attendanceviewt(request):
    form = attendanceview()
    if request.GET.get('subject'):
        dept = request.GET.get('department')
        sem = request.GET.get('semester')
        subject = request.GET.get('subject')
        date = request.GET.get('date')
        
        # Filter attendance records based on provided criteria
        results = Attendance.objects.filter(
            login_id__department__iexact=dept,
            login_id__semester=sem,
            subject__iexact=subject,
            current_date=date
        ).order_by('login_id__roll_number')

        if results:
            context = {
                'results': results,
                'dept': dept,
                'sem': sem,
                'subject': subject,
                'date': date
            }
            return render(request, 'attendance_results_teacher.html', context)
        else:
            messages.info(request, "No attendance records found for the given criteria.")
            
    return render(request, 'check_attendance_teacher.html', {'form': form})

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
    form = uploadmark()
    dept = request.GET.get('department')
    sem = request.GET.get('semester')
    
    # POST handler for bulk saving marks
    if request.method == 'POST' and 'upload_marks' in request.POST:
        dept = request.POST.get('dept')
        sem = int(request.POST.get('sem', 0))
        logid = request.session.get('t_id')
        teacher = get_object_or_404(teacherreg, login_id=logid)
        
        # Process existing students
        students = Studentreg.objects.filter(department=dept, semester=sem)
        for student in students:
            prefix = f"mark_{student.id}_"
            for key, value in request.POST.items():
                if key.startswith(prefix):
                    subject_name = key[len(prefix):]
                    if value.strip() != '':
                        try:
                            # Use get_or_create to ensure the mark entry exists
                            InternalMarks.objects.update_or_create(
                                subject=subject_name,
                                stud_id=student,
                                defaults={'marks': int(value), 'login_id': teacher}
                            )
                        except (ValueError, TypeError): pass
        
        # Process manually added new students
        # We look for rows indexed by number, e.g., manual_name_1, manual_roll_1, etc.
        item_keys = [k for k in request.POST.keys() if k.startswith('manual_name_')]
        for name_key in item_keys:
            idx = name_key.split('_')[-1]
            name = request.POST.get(f'manual_name_{idx}')
            roll = request.POST.get(f'manual_roll_{idx}')
            reg = request.POST.get(f'manual_reg_{idx}')
            
            if name and reg: # Minimum required to identify/create a student
                # Use reg (admno) as username for auto-login creation
                login_obj, created = Login.objects.get_or_create(
                    username=reg,
                    defaults={'password': '123', 'usertype': 1, 'status': 1}
                )
                
                # Ensure student is tied to this dept/sem even if they existed before
                student_obj, s_created = Studentreg.objects.get_or_create(
                    admno=reg,
                    defaults={
                        'name': name,
                        'roll_number': roll,
                        'department': dept,
                        'semester': sem,
                        'login_id': login_obj,
                        'address': 'Manual Entry',
                        'gender': 'Not Set',
                        'dob': date.today(),
                        'contactno': '0000000000'
                    }
                )
                if not s_created:
                    student_obj.department = dept
                    student_obj.semester = sem
                    if name: student_obj.name = name
                    if roll: student_obj.roll_number = roll
                    student_obj.save()
                
                # Update info if student existed but was moved? (Optional)
                
                # Process marks for this new student
                mark_prefix = f"manual_mark_{idx}_"
                for m_key, m_val in request.POST.items():
                    if m_key.startswith(mark_prefix):
                        subject_name = m_key[len(mark_prefix):]
                        if m_val.strip() != '':
                            try:
                                InternalMarks.objects.update_or_create(
                                    subject=subject_name,
                                    stud_id=student_obj,
                                    defaults={'marks': int(m_val), 'login_id': teacher}
                                )
                            except ValueError: pass

        messages.success(request, f'Marks for {dept.upper()} Semester {sem} saved correctly.')
        return redirect('login')

    if dept and sem:
        try:
            sem_int = int(sem)
        except:
            sem_int = 0
        students = Studentreg.objects.filter(department=dept, semester=sem_int).order_by('roll_number')
        
        # We now ALLOW proceeding even if no students are found (teacher can add them manually)
        
        if True: # Always proceed to the sheet if dept/sem are selected
            # logic to get KTU defaults (Standard Engineering Subjects)
            ktu_defaults = {
                '1': ['Mathematics I', 'Engineering Physics', 'Engineering Chemistry', 'Engineering Graphics', 'Engineering Mechanics', 'Basic Civil Engineering', 'Basic Mechanical Engineering', 'Basic Electrical Engineering', 'Basic Electronics Engineering'],
                '2': ['Mathematics II', 'Physics/Chemistry', 'Graphics/Mechanics', 'Introduction to Computing', 'Professional Ethics'],
                '3': ['Discrete Mathematics', 'Data Structures', 'Logic System Design', 'Object Oriented Programming'],
                '4': ['Graph Theory', 'Computer Organization', 'Operating Systems', 'Design & Analysis of Algorithms'],
                '5': ['Formal Languages', 'Computer Networks', 'Microprocessors', 'Database Management', 'Management of Software Systems'],
                '6': ['Computer Networks', 'Compiler Design', 'Machine Learning', 'Computer Graphics', 'Disaster Management', 'Industrial Management'],
                '7': ['AI', 'Cloud Computing', 'Cryptography', 'Distributed Computing', 'Elective 1', 'Elective 2'],
                '8': ['Data Mining', 'Internet of Things', 'Embedded Systems', 'Elective 3', 'Elective 4']
            }
            
            # Special override for AI & DS in S6
            if dept == 'aids' and sem == '6':
                ktu_defaults['6'] = ['Computer Networks', 'Compiler Design', 'Machine Learning', 'Computer Graphics', 'Disaster Management', 'Industrial Management', 'Microprocessor Lab', 'Machine Learning Lab']
            
            all_subjects = []
            
            # 1. Gather all unique subjects for this dept/sem from DB
            subj_meta = Subject.objects.filter(dept=dept, sem=sem).first()
            if subj_meta:
                # Check related Courses and Electives
                for c in Course.objects.filter(subject=subj_meta):
                    if c.name not in all_subjects: all_subjects.append(c.name)
                for e in ElectiveCourse.objects.filter(subject=subj_meta):
                    if e.name not in all_subjects: all_subjects.append(e.name)
                
                # Check aggregate models
                for model in [Subjectadd, SubjectDetail]:
                    detail_obj = model.objects.filter(subject=subj_meta).first()
                    if detail_obj:
                        fields = ['major1', 'major2', 'major3', 'minorsone', 'minortwo', 'aeca', 'aecb', 'mdc', 'vac1', 'vac2', 'sec', 'elective1', 'elective2']
                        for field in fields:
                            val = getattr(detail_obj, field, None)
                            if val:
                                for s in val.split(','):
                                    s_clean = s.strip()
                                    if s_clean and s_clean not in all_subjects:
                                        all_subjects.append(s_clean)
            
            # 2. Use KTU defaults if nothing found in DB
            if not all_subjects:
                all_subjects = ktu_defaults.get(str(sem), ['Internal Subject 1', 'Internal Subject 2'])
            
            # 3. Supplemental: Subjects already having marks in DB for this branch/sem
            existing_marks_subjects = InternalMarks.objects.filter(
                stud_id__department=dept, 
                stud_id__semester=sem
            ).values_list('subject', flat=True).distinct()
            
            for ms in existing_marks_subjects:
                if ms and ms not in all_subjects:
                    all_subjects.append(ms)

            # 4. Supplemental: Subjects chosen by students
            # Some elective names might not be in the branch-wide list if they are custom-entered
            for student in students:
                selection = StudentSubjectSelection.objects.filter(student=student).first()
                if selection:
                    # Same fields
                    fields = [
                        'minorsone', 'minortwo', 'aeca', 'aecb', 'mdc', 
                        'vac1', 'vac2', 'sec', 'elective1', 'elective2'
                    ]
                    for field in fields:
                        val = getattr(selection, field, None)
                        if val:
                            for s in val.split(','):
                                s_clean = s.strip()
                                if s_clean and s_clean not in all_subjects:
                                    all_subjects.append(s_clean)

            # Sort subjects for display
            all_subjects = sorted(list(set(all_subjects)))

            student_data = []
            for student in students:
                # Get existing marks
                marks_queryset = InternalMarks.objects.filter(stud_id=student)
                marks_dict = {m.subject: m.marks for m in marks_queryset}
                
                # Check assigned subjects
                assigned = set()
                selection = StudentSubjectSelection.objects.filter(student=student).first()
                if selection:
                    if selection.subject:
                        sd = selection.subject
                        for f in ['major1', 'major2', 'major3']:
                            v = getattr(sd, f, None)
                            if v:
                                for s in v.split(','): assigned.add(s.strip())
                    for f in ['minorsone', 'minortwo', 'aeca', 'aecb', 'mdc', 'vac1', 'vac2', 'sec', 'elective1', 'elective2']:
                        v = getattr(selection, f, None)
                        if v:
                             for s in v.split(','): assigned.add(s.strip())
                
                # Prepare marks in the same order as subject_columns
                marks_ordered = []
                for sub in all_subjects:
                    marks_ordered.append({
                        'subject': sub,
                        'value': marks_dict.get(sub, ''),
                        'is_assigned': sub in assigned
                    })

                student_data.append({
                    'id': student.id,
                    'roll_number': student.roll_number or 'N/A',
                    'reg_no': student.admno,
                    'name': student.name,
                    'marks_list': marks_ordered
                })

            return render(request, 'markuploadviewt.html', {
                'students_data': student_data,
                'subject_columns': all_subjects,
                'dept': dept,
                'sem': sem
            })
            
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
    student = get_object_or_404(Studentreg, login_id=stud_id)
    
    # Map student dept code to Subject table's dept name
    dept_map = {
        'cse': 'CSE',
        'aids': 'AI & DS',
        'me': 'Mechanical Engineering',
        'ce': 'Civil Engineering',
        'ece': 'Electronics & Communication'
    }
    
    mapped_dept = dept_map.get(student.department.lower(), student.department)
    
    # Core/Elective subjects from schema
    schema_subjects = []
    subj_meta = Subject.objects.filter(dept__iexact=mapped_dept, sem=student.semester).first()
    if subj_meta:
        for model in [Subjectadd, SubjectDetail]:
            detail_obj = model.objects.filter(subject=subj_meta).first()
            if detail_obj:
                for field in ['major1', 'major2', 'major3']:
                    val = getattr(detail_obj, field, None)
                    if val:
                        for s in val.split(','):
                            s_clean = s.strip()
                            if s_clean and s_clean not in schema_subjects:
                                schema_subjects.append(s_clean)
                                
    # Fetch subjects from actual attendance records as well
    attendance_records = Attendance.objects.filter(login_id=student)
    recorded_subjects = list(attendance_records.values_list('subject', flat=True).distinct())
    
    # Combine both lists
    all_subjects = list(set(schema_subjects + recorded_subjects))
    all_subjects = [s for s in all_subjects if s] # Filter out empty strings
    
    total_present = attendance_records.filter(present=1).count()
    subject_attendance = []
    for sub in all_subjects:
        sub_present = attendance_records.filter(subject=sub, present=1).count()
        sub_total = attendance_records.filter(subject=sub).count()
        sub_percentage = (sub_present / sub_total * 100) if sub_total > 0 else 0
        
        subject_attendance.append({
            'name': sub,
            'branch': student.department.upper(),
            'sem': student.semester,
            'percentage': round(sub_percentage, 2)
        })

    # Overall percentage across everything
    total_recs = attendance_records.count()
    overall_percentage = (total_present / total_recs * 100) if total_recs > 0 else 0

    return render(request, 'studattendance.html', {
        'subject_attendance': subject_attendance,
        'overall_percentage': round(overall_percentage, 2)
    })

def stud_daily_attendance(request):
    stud_id = request.session.get('stud_id')
    student = get_object_or_404(Studentreg, login_id=stud_id)
    records = Attendance.objects.filter(login_id=student).order_by('-current_date')
    return render(request, 'stud_daily_attendance.html', {'records': records})

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
            messages.success(request, 'University Exam Notification added!')
            return redirect('adminexam') 
    else:
        form = Examdate()
    exams = exam.objects.all().order_by('date')
    return render(request, 'adminexam.html', {'form': form, 'exams': exams})

def studexamview(request):
    results =exam.objects.all()
    return render(request,'user.html',{'data':results})

def notifications(request):
    from datetime import date, timedelta
    stud_id = request.session.get('stud_id')
    login_id = get_object_or_404(Studentreg, login_id=stud_id)
    today = date.today()
    results = exam.objects.all().order_by('date')
    upcoming_alert = results.filter(date__lte=today + timedelta(days=2), date__gte=today)
    return render(request, 'notifications.html', {'data': results, 'upcoming_alert': upcoming_alert})
def notificationt(request):
    from datetime import date, timedelta
    te_id = request.session.get('t_id')
    today = date.today()
    results = exam.objects.all().order_by('date')
    upcoming_alert = results.filter(date__lte=today + timedelta(days=2), date__gte=today)
    return render(request, 'notificationt.html', {'data': results, 'upcoming_alert': upcoming_alert})

def delete_exam(request, id):
    e = get_object_or_404(exam, id=id)
    e.delete()
    return redirect('adminexam')

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
        client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
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
                uploaded_file = client.files.upload(file=temp_pdf_path)
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

    # 1. Gather all possible subjects for this student (Core + Electives)
    all_subjects = []
    
    # Get subjects defined by HOD for this dept/sem
    subj_meta = Subject.objects.filter(dept__iexact=st.department, sem__iexact=str(st.semester)).first()
    if subj_meta:
        for model in [Subjectadd, SubjectDetail]:
            detail_obj = model.objects.filter(subject=subj_meta).first()
            if detail_obj:
                fields = ['major1', 'major2', 'major3', 'minorsone', 'minortwo', 'aeca', 'aecb', 'mdc', 'vac1', 'vac2', 'sec', 'elective1', 'elective2']
                for field in fields:
                    val = getattr(detail_obj, field, None)
                    if val:
                        for s in val.split(','):
                            s_clean = s.strip()
                            if s_clean and s_clean not in all_subjects:
                                all_subjects.append(s_clean)

    # 2. Get subjects specifically chosen by the student
    selection = StudentSubjectSelection.objects.filter(student=st).first()
    chosen_subjects = []
    if selection:
        fields = ['minorsone', 'minortwo', 'aeca', 'aecb', 'mdc', 'vac1', 'vac2', 'sec', 'elective1', 'elective2']
        for field in fields:
            val = getattr(selection, field, None)
            if val:
                for s in val.split(','):
                    s_clean = s.strip()
                    if s_clean:
                        chosen_subjects.append(s_clean)
                        if s_clean not in all_subjects:
                            all_subjects.append(s_clean)

    # 3. Get existing marks and ensure those subjects are in the list
    marks_queryset = InternalMarks.objects.filter(stud_id=st)
    marks_dict = {m.subject.strip(): m.marks for m in marks_queryset}
    
    for sub_name in marks_dict.keys():
        if sub_name not in all_subjects:
            all_subjects.append(sub_name)
    
    # Organize subjects into Categories for a better UI
    # We'll just pass a list of (subject, mark, is_chosen) tuples
    subjects_with_marks = []
    for sub in all_subjects:
        mark = marks_dict.get(sub, 'Not Uploaded')
        subjects_with_marks.append({
            'name': sub,
            'mark': mark,
            'is_chosen': sub in chosen_subjects or any(sub in (getattr(SubjectDetail.objects.filter(subject=subj_meta).first(), f, '') or '') for f in ['major1', 'major2', 'major3'] if subj_meta and SubjectDetail.objects.filter(subject=subj_meta).exists())
        })

    # For simplicity in current template, just pass'core' and 'elective' lists as before if needed, 
    # but let's just pass one comprehensive list
    return render(request, 'viewsubject.html', {
        'student': st,
        'subjects_with_marks': subjects_with_marks,
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
        else:
            obj, created = InternalMarks.objects.update_or_create(
                subject=subject_name,
                stud_id=student,
                defaults={'marks': int(marks), 'login_id': teacher}
            )
            if created:
                messages.success(request, 'Marks uploaded successfully!')
            else:
                messages.success(request, 'Marks updated successfully!')
            # You can change redirect later if needed
            return redirect('uploadmarks')


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
        else:
            obj, created = InternalMarks.objects.update_or_create(
                subject=subject_name,
                stud_id=student,
                defaults={'marks': int(marks), 'login_id': teacher}
            )
            if created:
                messages.success(request, 'Marks uploaded successfully!')
            else:
                messages.success(request, 'Marks updated successfully!')
            # You can change redirect later if needed
            return redirect('uploadmarks')

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
        form = omr(request.POST, request.FILES)
        print(form)
        if form.is_valid():
            a = form.save(commit=False)
            a.login_id = login_details
            a.tc_id = tc_id
            a.save()
            import threading
            threading.Thread(target=process_omr_in_background, args=(a.id,)).start()
            return redirect('viewomr')
    else:
        form = omr()

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

def stud_mark_select(request):
    form = uploadmark()
    return render(request, 'stud_mark_select.html', {'form': form})

def stud_mark_view(request):
    dept = request.GET.get('department')
    sem = request.GET.get('semester')
    stud_id = request.session.get('stud_id')
    
    if not stud_id:
        return redirect('login')
        
    student = get_object_or_404(Studentreg, login_id=stud_id)
    
    if dept and sem:
        # Subject discovery logic
        all_subjects = []
        subj_meta = Subject.objects.filter(dept=dept, sem=sem).first()
        
        ktu_defaults = {
            '1': ['Mathematics I', 'Engineering Physics', 'Engineering Chemistry', 'Engineering Graphics', 'Engineering Mechanics', 'Basic Civil Engineering', 'Basic Mechanical Engineering', 'Basic Electrical Engineering', 'Basic Electronics Engineering'],
            '2': ['Mathematics II', 'Physics/Chemistry', 'Graphics/Mechanics', 'Introduction to Computing', 'Professional Ethics'],
            '3': ['Discrete Mathematics', 'Data Structures', 'Logic System Design', 'Object Oriented Programming'],
            '4': ['Graph Theory', 'Computer Organization', 'Operating Systems', 'Design & Analysis of Algorithms'],
            '5': ['Formal Languages', 'Computer Networks', 'Microprocessors', 'Database Management', 'Management of Software Systems'],
            '6': ['Computer Networks', 'Compiler Design', 'Machine Learning', 'Computer Graphics', 'Disaster Management', 'Industrial Management'],
            '7': ['AI', 'Cloud Computing', 'Cryptography', 'Distributed Computing', 'Elective 1', 'Elective 2'],
            '8': ['Data Mining', 'Internet of Things', 'Embedded Systems', 'Elective 3', 'Elective 4']
        }
        
        if dept == 'aids' and sem == '6':
            ktu_defaults['6'] = ['Computer Networks', 'Compiler Design', 'Machine Learning', 'Computer Graphics', 'Disaster Management', 'Industrial Management', 'Microprocessor Lab', 'Machine Learning Lab']
        
        all_subjects.extend(ktu_defaults.get(sem, []))
        
        if subj_meta:
            for model in [Subjectadd, SubjectDetail]:
                detail_obj = model.objects.filter(subject=subj_meta).first()
                if detail_obj:
                    fields = ['major1', 'major2', 'major3', 'minorsone', 'minortwo', 'aeca', 'aecb', 'mdc', 'vac1', 'vac2', 'sec', 'elective1', 'elective2']
                    for field in fields:
                        val = getattr(detail_obj, field, None)
                        if val:
                            for s in val.split(','):
                                s_clean = s.strip()
                                if s_clean and s_clean not in all_subjects: all_subjects.append(s_clean)
        
        # Student specific selection
        selection = StudentSubjectSelection.objects.filter(student=student).first()
        if selection:
            fields = ['minorsone', 'minortwo', 'aeca', 'aecb', 'mdc', 'vac1', 'vac2', 'sec', 'elective1', 'elective2']
            for field in fields:
                val = getattr(selection, field, None)
                if val:
                    for s in val.split(','):
                        s_clean = s.strip()
                        if s_clean and s_clean not in all_subjects: all_subjects.append(s_clean)

        # Subjects with marks
        marks_queryset = InternalMarks.objects.filter(stud_id=student)
        marks_dict = {m.subject.strip(): m.marks for m in marks_queryset}
        for sub_name in marks_dict.keys():
            if sub_name not in all_subjects: all_subjects.append(sub_name)

        all_subjects = sorted(list(set(all_subjects)))
        
        # Assigned subjects set
        assigned = set()
        if selection:
            if selection.subject:
                sd = selection.subject
                for f in ['major1', 'major2', 'major3']:
                    v = getattr(sd, f, None)
                    if v:
                        for s in v.split(','): assigned.add(s.strip())
            for f in ['minorsone', 'minortwo', 'aeca', 'aecb', 'mdc', 'vac1', 'vac2', 'sec', 'elective1', 'elective2']:
                v = getattr(selection, f, None)
                if v:
                     for s in v.split(','): assigned.add(s.strip())

        marks_ordered = []
        for sub in all_subjects:
            marks_ordered.append({
                'subject': sub,
                'value': marks_dict.get(sub, ''),
                'is_assigned': sub in assigned
            })

        student_data = {
            'roll_number': student.roll_number or 'N/A',
            'reg_no': student.admno,
            'name': student.name,
            'marks_list': marks_ordered
        }

        return render(request, 'stud_mark_view.html', {
            'student_data': student_data,
            'subject_columns': all_subjects,
            'dept': dept,
            'sem': sem
        })
        
    return redirect('stud_mark_select')
