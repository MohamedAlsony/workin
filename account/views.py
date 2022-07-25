from mysite.tasks import CVParsing
from rest_framework.authentication import TokenAuthentication
from rest_framework import status
from account.models import Account,AccountCode,Profile
from rest_framework import generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import authentication, permissions
from rest_framework.decorators import *
from account.serializers import *
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
import pytz
from datetime import datetime
from cryptography.fernet import InvalidToken
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from cryptography.fernet import Fernet
from mysite.tasks import SendMail
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.parsers import FileUploadParser, JSONParser, MultiPartParser,DataAndFiles, BaseParser
import pandas as pd

# Register API
class RegisterAPI(APIView):
    authentication_classes = []
    permission_classes = []
    serializer_class = RegistrationSerializer
    @swagger_auto_schema(request_body=openapi.Schema(
     type=openapi.TYPE_OBJECT,
     properties={
        'email': openapi.Schema(type=openapi.TYPE_STRING , description='email'),
		'firstname': openapi.Schema(type=openapi.TYPE_STRING , description='firstname'),
		'lastname': openapi.Schema(type=openapi.TYPE_STRING , description='lastname'),
        'password': openapi.Schema(type=openapi.TYPE_STRING  , description='password')
     }),
     responses={200: RegistrationSerializer, 400 : 'Bad Request'})

    def post(self, request, *args, **kwargs):
        print(f'\n{request.data}')
        print(request.data.get('email'))
        context = {}
        email = request.data.get('email').lower()


       #check email if already exist send error

        if Account.objects.filter(email=email).count()>0:
            context['error_message'] = 'That email is already in use.'
            context['response'] = 'error'
            return Response(data=context)


       # Assign serializer
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            #if valid save object and send response
            account = serializer.save()
            context['email'] = account.email
            context['firstname'] = account.firstname
            context['lastname'] = account.lastname
            context['pk'] = account.pk
            token = Token.objects.get(user=account).key
            context['token'] = token
            context['is_verified'] = account.verified
            context['is_company'] = account.is_company
            context['response'] = 'success'
            return Response(data=context)


        #if not valid return error
        context = serializer.errors.copy()
        context['response'] = 'error'
        return Response(data=context)



class LoginAPI(APIView):
    authentication_classes = []
    permission_classes = []
    serializer_class = UserProfileSerializer
    @swagger_auto_schema(request_body=openapi.Schema(
      type=openapi.TYPE_OBJECT,
      properties={
        'email': openapi.Schema(type=openapi.TYPE_STRING , description='email'),
        'password': openapi.Schema(type=openapi.TYPE_STRING  , description='password')
      }),
	  responses={200: RegistrationSerializer,400: 'Bad Request'})
    def post(self, request, *args, **kwargs):
        print(f'\n{request.data}')
        context = {}
        email = request.data.get('email')
        password = request.data.get('password')
        account = authenticate(email=email, password=password)
        if account:
            try:
                token = Token.objects.get(user=account)
            except Token.DoesNotExist:
                token = Token.objects.create(user=account)
            context['response'] = 'success'
            context['pk'] = account.pk
            context['email'] = email.lower()
            context['token'] = token.key
            context['is_verified'] = account.verified
            context['is_company'] = account.is_company
            context['firstname'] = account.firstname
            context['lastname'] = account.lastname
            #print(account)
            #print(context)
            profile_created = False
            try:
                profile = account.profile
                serializer = self.serializer_class(profile)
                context.update(serializer.data)
                profile_created = True
            except Account.profile.RelatedObjectDoesNotExist:
                pass
			#context= {**context,**serializer.data.copy()}??
            context['profile_created'] = profile_created
            return Response(data=context)
        context['response'] = 'Error'
        context['error_message'] = 'Invalid credentials'
        return Response(data=context)

@api_view(['POST', ])
@permission_classes([])
@authentication_classes([])
@permission_classes([])

def check_verification_mail(request):

	if request.method == 'POST':
		print(f'\n{request.data}')
		data = {}
		email = request.data.get('email').lower()
		try:
			account = Account.objects.get(email=email)

		except Account.DoesNotExist:
			data['response'] = 'error'
			data['error_msg'] = "Account does not exist"
			return Response(data)


		#request.user.verify()
		account.verify()
		data['response'] = 'success'
		data['email'] = account.email
		return Response(data)


@api_view(['POST', ])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def user_verification(request):
    print(f'\n{request.data}')
    data = {}
    if request.method == 'POST':
        #email = request.data.get('email').lower()


        verifycode = request.data.get('verification_code')
        account = request.user

        codes = AccountCode.objects.filter(user=account.pk)
        if codes.count() == 0:
            return Response({'response':'error', 'error_msg':'something went wrong!'})

        if verifycode == codes[0].verification_code:

            data['email'] = account.email
            data['response'] = 'success'
            data['token'] = request.auth.key
            account.verified = True
            account.save()
            return Response(data)

        data['response'] = 'error'
        data['error_msg'] = 'invalid code'
        return Response(data)






def encryption(token, mode, key):
    # create object fernet to encrypt or decrypt
	fernet = Fernet(key)
    #e = encrypt
	if mode == 'e':
        #encode token then encrypt
		encMessage = fernet.encrypt(token.encode())
		return encMessage.decode()
    #d = decrypted
	elif mode=='d':
        #decrypt message
		try:
			decMessage = fernet.decrypt(token.encode()).decode()
		except InvalidToken:
			decMessage = ''
		return decMessage
	return None


@api_view(['POST', ])
@permission_classes([])
@authentication_classes([])
def check_reset_password_mail(request):
	print(f'\n{request.data}')
	if request.method == 'POST':
		data = {}
		email = request.data.get('email').lower()
		try:
			account = Account.objects.get(email=email)
		except Account.DoesNotExist:
			data['response'] = 'error'
			data['error_msg'] = "Account does not exist"
			return Response(data)

		codes = AccountCode.objects.filter(user= account.pk)
		tz = pytz.timezone('UTC')
		now = datetime.now(tz)

		if codes.count()==0:
			codes = AccountCode.objects.create(user=account, date=now , date2=now , date3=now)
			codes.renew_reset_password()
			codes.save()
		else:
			codes = codes[0]
			codes.renew_reset_password()
		period = (codes.date2 - codes.date).seconds // 60

		if codes.freeze:
			x = (now - codes.date3).seconds // 60
			if x < 60:
				return Response({'response': 'error', 'error_msg': f'you are blocked for {60 - x} minutes'})

		x = (now - codes.date2).days

		if x >= 1:
			codes.foul_count = max(0, codes.foul_count-1)
			codes.resend_count = 0
			codes.block = False
		if not codes.block:
			if codes.resend_count < 10:

				if period < 60:
					codes.resend_count += 1
					codes.date2 = now
				else:

					codes.resend_count = 1
					codes.date = now
					codes.date2 = now
			else:
				if codes.foul_count >= 2:
					codes.block = True
					codes.save()
					return Response({'response':'error', 'error_msg':'you are blocked for one day'})
				if codes.freeze:
					codes.freeze = False
					codes.resend_count = 0
					codes.date = now
					codes.date2 = now
				else:
					codes.date3 = now
					codes.freeze = True
					codes.date2 = now
					codes.date = now
					codes.save()
					return Response({'response': 'error', 'error_msg': f'you are blocked for {60} minutes'})

				if codes.foul_count >= 2:
					codes.block = True
					codes.save()
					return Response({'response':'error', 'error_msg':'you are blocked for one day'})
				else:
					codes.foul_count += 1
					codes.resend_count = 1
		else:
			return Response({'response': 'error', 'error_msg': 'you are blocked for one day'})

		codes.save()
		subject = f'hi {account.firstname}, this mail is for your new password'
		body = f'your reset password code is: {codes.reset_password}'
		SendMail(subject,body, email).start()
		data['response'] = 'success'
		key = b'S5RsmrVWsyxD9XU07M1pp3Iza-iJX7QT8KEo52-E5l4='
		t = Token.objects.get(user=account).key
		token = encryption(t, 'e', key)
		data['token'] = token
		data['email'] = account.email
		return Response(data)

@api_view(['POST', ])
@permission_classes([])
@authentication_classes([])
def check_reset_password_code(request, token):

	print(f'\n{request.data}')
	print(f'token entered in url: {token}')
	data = {}
	email = request.data.get('email').lower()
	try:
		account = Account.objects.get(email=email)
	except Account.DoesNotExist:
		data['response'] = 'error'
		data['error_msg'] = "Account does not exist"
		return Response(data)

	key = b'S5RsmrVWsyxD9XU07M1pp3Iza-iJX7QT8KEo52-E5l4='
	token = encryption(token, 'd', key)
	account_token = Token.objects.get(user=account).key
	if token != account_token:
		data['response'] = 'error'
		data['error_msg'] = "Account does not exist"
		return Response(data)

	if request.method == 'POST':

		reset_password_code = request.data.get('reset_password_code')

		codes = AccountCode.objects.filter(user=account.pk)
		if codes.count() == 0:
			return Response({'response':'error'})
		if reset_password_code == codes[0].reset_password:
			key = b'TQXelGorbDLwLdhklkXcDpySpMiW8jHuMzw3tpH-gok='
			token = encryption(token, 'e', key)
			data['response'] = 'success'
			data['token'] = token
			data['email'] = account.email
			return Response(data)
		data['response'] = 'error'
		data['error_msg'] = 'invalid code'
		return Response(data)

@api_view(['POST', ])
@permission_classes([])
@authentication_classes([])
def reset_password(request, token):
	print(f'\n{request.data}')
	print(f'token entered in url: {token}')
	data = {}
	email = request.data.get('email')
	try:
		account = Account.objects.get(email=email)
	except Account.DoesNotExist:
		data['response'] = 'error'
		data['error_msg'] = "Account does not exist"
		return Response(data)


	key = b'TQXelGorbDLwLdhklkXcDpySpMiW8jHuMzw3tpH-gok='
	token = encryption(token, 'd', key)
	account_token = Token.objects.get(user=account).key
	if token != account_token:
		data['response'] = 'error'
		data['error_msg'] = "Account does not exist"
		return Response(data)


	if request.method == 'POST':


		password = request.data.get('password')
		password2 = request.data.get('password2')

		try:
			validate_password(password)
		except ValidationError as val_err:
			data['response'] = 'error'
			data['error_msg'] = ' '.join(val_err.messages)
			return Response(data)

		if password != password2:
			data['response'] = 'error'
			data['error_msg'] = 'Passwords must match.'
			return Response(data)


		account.set_password(password)
		account.save()
		data['response'] = 'success'

		#codes = AccountCode.objects.filter(user=account.pk)
	    #if codes.count()>0:
		#	codes[0].

		return Response(data)


class UserProfileAPI(APIView):

    authentication_classes     = []
    permission_classes         = []
    serializer_class           = UserProfileSerializer


    @swagger_auto_schema(request_body=openapi.Schema(
     type=openapi.TYPE_OBJECT,
     properties={
        'email': openapi.Schema(type=openapi.TYPE_STRING , description='email  + the data from the response without the user field'),
     }),
     responses={200: UserProfileSerializer, 400 : 'Bad Request'})
    def post(self, request, *args, **kwargs):
        print(f'\n{request.data}')
        context  = {}
        email    = request.data.get('email')
        email    = email.lower() if email else None
        account  = Account.objects.filter(email=email)



       # if account exists

        if account.count() == 0 :
            context['error_message'] = 'Account not found.'
            context['response'] = 'error'
            return Response(data=context)


       # Assign serializer
        account= account[0]
        data = request.data.copy()
        #set relation
        data['user'] = account.pk
        serializer = self.serializer_class(data=data)

        if serializer.is_valid():
            #if valid save object and send response
            serializer.save()
            context['email']       = account.email
            context['is_verified'] = account.verified
            context['is_company']  = account.is_company
            context['firstname']   = account.firstname
            context['lastname']    = account.lastname
            #** turn dictioanries into vars and copy values from serailizer
            context= {**context,**serializer.data.copy()}
            context['response']    = "Success"

            print(context)
            return Response(data=context)



        else:
            error_msg =''
            data = serializer.errors.copy()
            for i in data:
                error_msg += ', '.join(data[i]) + '\n'

            context['response'] = 'error'
            if 'user' in data:
                error_msg = 'This email already exists.'
            context['error_message'] = error_msg
            return Response(data=context)

class UserProfileSetup(APIView):
    authentication_classes     = []
    permission_classes         = []
    serializer_class           = UserProfileSerializer

    @swagger_auto_schema(request_body=openapi.Schema(
     type=openapi.TYPE_OBJECT,
     properties={
        'email': openapi.Schema(type=openapi.TYPE_STRING , description='email  + the data from the response without the user field'),
     }),
     responses={200: UserProfileSerializer, 400 : 'Bad Request'})
    def post(self, request, *args, **kwargs):
        print(f'\n{request.data}')

        context = {}
        email = request.data.get('email')
        email = email.lower() if email else None
        #profile class in database #select related = join in sql
        account     = Account.objects.select_related('profile').filter(email=email)




        if account.count() == 0:
            context['response'] = 'Error'
            context['error_message'] = 'email not registered'
            return Response(data=context)

        account = account[0]

        data = request.data.copy()

        try:
            profile = account.profile
        except Account.profile.RelatedObjectDoesNotExist:
            context = {"response":"error", "error_msg":" profile not exist"}
            return Response(data=context)

        serializer=self.serializer_class(profile, data=data, partial=True)


        if serializer.is_valid():
            #if valid save object and send response
            serializer.save()

            context['email']       = account.email
            context['is_company']  = account.is_company
            context['firstname']   = account.firstname
            context['lastname']    = account.lastname
            #** turn dictioanries into vars and copy values from serailizer
            context= {**context,**serializer.data.copy()}

            context['response']    = "Success"

            print(context)
            return Response(data=context)



        else:

            context = serializer.errors.copy()
            context['response'] = 'error'
            return Response(data=context)


class FileUploadView(APIView):

    permission_classes = []
    parser_class = (FileUploadParser,)



    @swagger_auto_schema(request_body=openapi.Schema(
     type=openapi.TYPE_OBJECT,
     properties={
     'email': openapi.Schema(type=openapi.TYPE_STRING , description='email in the url'),
     'file' :  openapi.Schema(type=openapi.TYPE_FILE , description='.pdf or imgs '),
     }),
     responses={201: FileSerializer , 400 : 'Bad Request'})
    def post(self, request, *args, **kwargs):
        from copy import deepcopy
        print(f'\n{request.data}')
        #print(dir(request.stream.body))
        context={}
        #to retrieve email from url
        email = request.GET.get('email')
        print(request.data)
        #print(dir(request.stream))

        email = email.lower() if email else None
        account = Account.objects.filter(email=email)

        if account.count() == 0:
            context['response'] = 'Error'
            context['error_message'] = 'email not found'
            return Response(data=context)

        account = account[0]


        cv_parsing = CVParsing(deepcopy(request.FILES.get('file')))
        cv_parsing.start()

        # file_pth = Path("Marwancv.pdf")

        context['file'] = request.FILES.get('file')
        #print('zzz')
        #print(request.FILES.get('file').open('rb').readlines(5))


        file_serializer = FileSerializer(account ,data=context)

        if file_serializer.is_valid():
            file_serializer.save()
            context= {**context,**file_serializer.data.copy()}
            context['response']    = "Success"
            cv_data = cv_parsing.join_with_return()
            context.update(cv_data)
            #print(cv_data)

            print(context)
            return Response(context)
        else:
            return Response(file_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserDetailView(APIView):

    permission_classes = []
    serializer_class = UserProfileSerializer
    @swagger_auto_schema(operation_description = " Email of the user in the url, return the user profile")
    def get(self, request, email):
        profile = Profile.objects.select_related('user').filter(user__email = email).first()
        if not profile:
            return Response({'response': 'error', 'error_msg':'invalid email'})
        context = self.serializer_class(profile).data.copy()
        context['firstname'] = profile.user.firstname
        context['lastname'] = profile.user.lastname
        context['email'] = email
        return Response(context)

class PictureUploadView(APIView):

    permission_classes = []
    parser_class = (MultiPartParser, JSONParser)



    @swagger_auto_schema(request_body=openapi.Schema(
     type=openapi.TYPE_OBJECT,
     properties={
     'email': openapi.Schema(type=openapi.TYPE_STRING , description='email in the url'),
     'picture' :  openapi.Schema(type=openapi.TYPE_FILE , description='.pdf or imgs '),
     }),
     responses={201: PictureSerializer , 400 : 'Bad Request'})
    def post(self, request, *args, **kwargs):
        print(f'\n{request.data}')
        #print(dir(request.stream.body))
        context={}
        #to retrieve email from url
        email = request.GET.get('email')
        print(request.data)
        #print(dir(request.stream))

        email = email.lower() if email else None
        account = Profile.objects.filter(user__email=email)

        if account.count() == 0:
            context['response'] = 'Error'
            context['error_message'] = 'email not found'
            return Response(data=context)

        account = account[0]

        context['picture'] = request.FILES.get('picture')

        file_serializer = PictureSerializer(account ,data=context)

        if file_serializer.is_valid():
            context = {}
            account = file_serializer.save()
            if account.picture:
                context['picture'] = account.picture.url
            else: context['picture'] = ''

            context['response']    = "Success"
            return Response(data= context, status=status.HTTP_201_CREATED)
        else:
            return Response(file_serializer.errors, status=status.HTTP_400_BAD_REQUEST)






