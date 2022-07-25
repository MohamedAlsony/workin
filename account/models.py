
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token
from datetime import datetime
from django.core.exceptions import ValidationError
import math,random
import re
from cloudinary.models import CloudinaryField





class MyAccountManager(BaseUserManager):
	def create_user(self, email, password=None):
		if not email:
			raise ValueError('Users must have an email address')


		user = self.model(
			email=self.normalize_email(email),
		)

		user.set_password(password)
		user.save(using=self._db)
		return user


	def create_superuser(self, email, password):
		user = self.create_user(
			email=self.normalize_email(email),
			password=password,
		)
		user.is_admin = True
		user.is_staff = True
		user.is_superuser = True
		user.save(using=self._db)
		return user


class Account(AbstractBaseUser):
	email                   = models.EmailField(verbose_name="email", max_length=60, unique=True)
	username 				= None
	firstname               = models.CharField(max_length=25,null = False,default="firstname")
	lastname                = models.CharField(max_length=25,null = False,default="lastname")
	file = CloudinaryField(resource_type="auto", null=True, blank=True)
	date_joined				= models.DateTimeField(verbose_name='date joined', auto_now_add=True)
	last_login				= models.DateTimeField(verbose_name='last login', auto_now=True)
	#add boolean field to differentiate between users and companies
	is_company				= models.BooleanField(default=False)
	is_admin				= models.BooleanField(default=False)
	is_active				= models.BooleanField(default=True)
	is_staff				= models.BooleanField(default=False)
	is_superuser			= models.BooleanField(default=False)
	verified                = models.BooleanField(default=False)



	USERNAME_FIELD = 'email'
	REQUIRED_FIELDS = []

	objects = MyAccountManager()

	def __str__(self):
		return self.email

	def clean(self):
		if not bool(re.fullmatch('[A-Za-z]{2,25}( [A-Za-z]{2,25})?',self.firstname)):
			raise ValidationError(
			{'firstname': "names must not contain digits!"})

		if not bool(re.fullmatch('[A-Za-z]{2,25}( [A-Za-z]{2,25})?',self.lastname)) :
			raise ValidationError(
                {'lastname': "names must not contain digits!"})









	def verify(self):
		from mysite.tasks import SendMail, SendVerificationMail
		email =self.email

		digits = "0123456789"
		OTP = ""
		for i in range(6):
			OTP += digits[math.floor(random.random() * 10)]
			codes = AccountCode.objects.filter(user=self.pk)
		if codes.count() == 0:
			codes = AccountCode.objects.create(user=self, verification_code = OTP)
		else:
			codes = codes[0]
		codes.verification_code = OTP
		codes.save()
		subject = f'hi {self.firstname}, this mail is for your verification code:'
		#body = f'your verification code is: {codes.verification_code}'
		SendVerificationMail(subject=subject, to=email, code=codes.verification_code).start()









	# For checking permissions. to keep it simple all admin have ALL permissons
	def has_perm(self, perm, obj=None):
		return self.is_admin

	# Does this user have permission to view this app? (ALWAYS YES FOR SIMPLICITY)
	def has_module_perms(self, app_label):
		return True


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
	if created:
		Token.objects.create(user=instance)
		instance.verify()




class AccountCode(models.Model):
	user              = models.OneToOneField(Account, on_delete=models.CASCADE)
	verification_code = models.CharField(max_length=6, null=False, blank=False)
	reset_password    = models.CharField(max_length=6, null=False, blank=False)
	resend_count      = models.PositiveSmallIntegerField(default=0, blank=True)
	date              = models.DateTimeField(blank=True, default=datetime.now)
	date2             = models.DateTimeField(blank=True, default=datetime.now)
	date3             = models.DateTimeField(blank=True, default=datetime.now)
	block             = models.BooleanField(blank=True, default=False)
	freeze            = models.BooleanField(blank=True, default=False)
	foul_count        = models.PositiveSmallIntegerField(blank=True, default=0)


	def renew_reset_password(self):
		digits = "0123456789"
		OTP = ""
		for i in range(6):
			OTP += digits[math.floor(random.random() * 10)]
		self.reset_password = OTP
		self.save()



'''
Data
4- number
5- career level(student-entery level -junior-senior-management)
6-type of job(full time - half time -intership-shift based - working from home -volunteering)
7-job careers interested in (software engineering-translation- architecture-design )

8-job title looking for(android developer-ux designer-ui designer- frontend developer)

9- min salary
10-skills
11-birthdate(days- months-years)
12-gender
13- nationality (magmo3et belad 7elwa keda )
14-location ( country-city - area) zy ely ableha
15- years of experience
16- current education level( student- bachelor-under grad-master’s-phd)
17- field of study (computer science-engineering- fine arts-arts)
18- uni
19- year of grad (years)
20- gpa
21- languages ( arabic - English-french - german- spanish - italian - Chinese )

'''

class Profile(models.Model):


	user = models.OneToOneField(Account,on_delete=models.CASCADE,primary_key=True,)


	career_level_choices = [("ST","Student"),("EL","Entrylevel"),("JR","Junior")
		,("Sr","Senior"),("MGT","Management")]

	job_types_choices   = [("FT","Full time"),("HT","Half time"),("IN","Intership"),("SB","Shift based"),("WFH","Work from home"),("VN","Volunteering")]

	intrested_careers_choices = [("SE","Software Engineering"),("ARCH","Architecture")
		,("TR","Translation"),("DES","Design") ]

	genders_choices=[("M","Male"),("F","Female")]

	education_level_choices = [("ST","Student"),("BCH","Bachelor"),("UG","UnderGrad"),("MST","Masters"),("PHD","PHD")]

	study_Field_choices =[("Cs","Computer Science"),("ENG","Engineering"),("FA","Fine Arts"),("AS","Arts")]

	langs =[("DU","Deutsch"),("FR","French"),("En","English"),("AR","Arabic")]

	nationality  = models.CharField(max_length=20,null=True, default='')

	phone_number = models.CharField(max_length=13,null=True, default='')

	job_title_looking_for   = models.CharField(max_length=30,null= True, default='')

	career_level = models.CharField(max_length=50,default="Junior",null=True)

	job_types = models.CharField(max_length=50,default='FT',null=True)

	careers_intrests = models.CharField(max_length=50,default='SE')

	min_salary =models.PositiveIntegerField(null=True, default=0)

	skills=models.CharField(max_length=200,null=True, default='')

	birthdate = models.DateField(null=True)

	gender = models.CharField(max_length=15,choices=genders_choices,default="M")

	location=models.CharField(max_length=50,null=True, default='')

	country = models.CharField(max_length=50,null=True, default='')

	city    = models.CharField(max_length=50,null=True, default='')

	area    = models.CharField(max_length=50,null=True, default='')

	years_of_experience=models.PositiveIntegerField(null=True, default=0)

	education_level = models.CharField(max_length=50,default="BCH",null=True)

	study_fields     = models.CharField(max_length=50,default="ENG",null=True)

	uni = models.CharField(max_length=50,null=True, default='')



	about = models.CharField(max_length=500,null=True,blank=True, default='')

	yearofgrad= models.PositiveSmallIntegerField(null=True,blank=True, default= 2022)

	gpa = models.CharField(max_length=4,null=True, default='')

	languages= models.CharField(max_length=20,default="En",null=True)

	language_level= models.CharField(max_length=20,null=True,blank=True, default='')
	picture = CloudinaryField(resource_type="auto", null=True, blank=True)

	def __str__(self):
		return self.user.email



