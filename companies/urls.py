from django.conf.urls import url
from django.urls import path, include
from companies.views import *

urlpatterns = [

 path('register/',Company_RegisterAPI.as_view()),
 path('register/2',CompanyProfileAPI.as_view()),
 path('login/',Company_LoginAPI.as_view()),
 path('Profile_setup/',CompanyProfileSetup.as_view()),
 path('upload_logo',LogoUploadView.as_view()),
 path('review/<str:company_email>',ReviewApi.as_view()),
 path('show_reviews/<str:company_email>',Reviewlist.as_view()),
 path('<str:email>',CompanyDetailApi.as_view()),

]

