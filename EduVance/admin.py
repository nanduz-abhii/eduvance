from django.contrib import admin
from .models import teacherreg, Login, AssignmentQuestion, Assignment

admin.site.register(teacherreg)
admin.site.register(Login)
admin.site.register(AssignmentQuestion)
admin.site.register(Assignment)
