import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'majorp.settings')
django.setup()

from django.contrib.auth.models import User
from EduVance.models import Login, Studentreg, teacherreg

print("Deleting Custom Application Users...")
Login.objects.all().delete()
print("Custom users deleted.")

print("Creating Admin User...")
admin_login = Login.objects.create(username="admin", password="admin@123", usertype=3, status=1)

print("Creating Teacher User...")
teacher_login = Login.objects.create(username="teacher", password="teacher@123", usertype=2, status=1)
teacherreg.objects.create(
    login_id=teacher_login,
    tname="Test Teacher",
    tgender="Other",
    tdepartment="CS",
    tcontactno="0000000000"
)

print("Creating Student User...")
student_login = Login.objects.create(username="student", password="student@123", usertype=1, status=1)
Studentreg.objects.create(
    login_id=student_login,
    admno="TEST1",
    name="Test Student",
    gender="Other",
    dob="2000-01-01",
    department="CS",
    semester=1,
    contactno="0000000000"
)

print("Users reset successfully.")
