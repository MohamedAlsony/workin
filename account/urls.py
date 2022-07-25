from django.conf.urls import url
from django.urls import path, include
from account.views import *


urlpatterns = [
 path('register/',RegisterAPI.as_view()),
 path('login/',LoginAPI.as_view()),
 path('reset_password_mail/', check_reset_password_mail, name="check_if_account_exists"),
 path('reset_password_check/<str:token>/', check_reset_password_code, name="check_if_account_code"),
 path('reset_password/<str:token>/', reset_password, name="reset_password"),
 path('send_verification_mail/',check_verification_mail,),
 path('user_verification',user_verification),
 path('user_profile/',UserProfileAPI.as_view()),
 path('user_profile_update/',UserProfileSetup.as_view()),
 path('upload_file',FileUploadView.as_view()),
 path('upload_picture',PictureUploadView.as_view()),
 path('user_detail/<str:email>',UserDetailView.as_view())
]

