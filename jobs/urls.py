from django.conf.urls import url
from django.urls import path, include
from jobs.views import *

urlpatterns = [

 path('create_job',JobCreation.as_view()),
 path('job_detail/<int:job>',JobDetail.as_view()),
 path('company_job_detail/<int:job>',CompanyJobDetail.as_view()),
 path('job_apply/<int:job>',JobApply.as_view()),
 path('company_jobs/<str:email>',CompanyJobs.as_view()),
 path('user_jobs',AppliedJobs.as_view()),
 path('home_screen/',HomeScreen.as_view()),
 path('recommended_users/<int:job>',users_recommended.as_view()),
 path('SendEmail/',SendMail.as_view()),
 path('Search/<str:search>',Search.as_view()),]
