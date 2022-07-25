from thefuzz import fuzz
from rest_framework.authentication import TokenAuthentication
from django.db.models import Case, When, Q
from mysite.tasks import CVParsing
from rest_framework import status
from account.models import Account, AccountCode, Profile
from rest_framework import generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import authentication, permissions
from rest_framework.decorators import *
from account.serializers import *
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from cryptography.fernet import InvalidToken
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from cryptography.fernet import Fernet
from mysite.tasks import SendMail
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.parsers import FileUploadParser, JSONParser, MultiPartParser, DataAndFiles, BaseParser
from jobs.models import Jobs
from jobs.serializers import *


class JobCreation(APIView):
    authentication_classes = [TokenAuthentication, ]
    permission_classes = [IsAuthenticated]
    serializer_class = JobSerializer

    @swagger_auto_schema(operation_description="headers = {'Authorization': 'Token {token}'}  Company token",
                         request_body=openapi.Schema(
                             type=openapi.TYPE_OBJECT,

                             properties={
                                 'Same data of the response example': openapi.Schema(type=openapi.TYPE_STRING,
                                                                                     description='7abeby'),
                             }),

                         responses={200: serializer_class, 400: 'Bad Request'})
    def post(self, request, *args, **kwargs):

        context = {}
        if not request.user.is_company:
            context['response'] = 'error'
            context['error'] = 'you are not allowed to access this API'

            return Response(data=context)

        data = request.data.copy()
        data['company'] = request.user.companyprofile
        # set relation
        serializer = self.serializer_class(data=data)

        if serializer.is_valid():
            # if valid save object and send response
            serializer.save()
            # ** turn dictioanries into vars and copy values from serailizer
            context = {**context, **serializer.data.copy()}
            context['response'] = "Success"

            return Response(data=context)



        else:

            context = serializer.errors.copy()
            context['response'] = 'error'
            return Response(data=context)


class JobDetail(APIView):
    authentication_classes = []
    permission_classes = []
    serializer_class = JobSerializer

    @swagger_auto_schema(operation_description="Job primarykey in the url to view the job detail")
    def get(self, request, job):
        context = {}
        job = Jobs.objects.filter(pk=job)
        if job.count() == 0:
            context['response'] = 'error'
            context['error'] = 'job doesnt exist'
            return Response(data=context)

        job_detail = job[0]

        serializer = self.serializer_class(job_detail)
        context = {**context, **serializer.data.copy()}
        context['response'] = 'success'
        return Response(data=context)


class CompanyJobDetail(APIView):
    authentication_classes = []
    permission_classes = [IsAuthenticated]
    serializer_class = CompanyJobSerializer

    @swagger_auto_schema(
        operation_description="headers = {'Authorization': 'Token {token}'} Company token, job primary key in url")
    def get(self, request, job):
        context = {}
        job = Jobs.objects.filter(pk=job).first()
        if not job:
            context['response'] = 'error'
            context['error'] = "job doesn\'t exist"
            return Response(data=context)
        if not request.user.is_company:
            context['response'] = 'error'
            context['error'] = "not allowed"
            return Response(data=context)

        serializer = self.serializer_class(job)
        context = {**context, **serializer.data}
        context['response'] = 'success'
        return Response(data=context)


class JobApply(APIView):
    authentication_classes = [IsAuthenticated]
    permission_classes = []
    serializer_class = JobSerializer

    @swagger_auto_schema(operation_description="headers = {'Authorization': 'Token {token}'} User token",
                         request_body=openapi.Schema(
                             type=openapi.TYPE_OBJECT,
                             properties={
                                 'job pk': openapi.Schema(type=openapi.TYPE_STRING, description=' In url'),

                             }),
                         responses={201: JobSerializer, 400: 'Bad Request'})
    def post(self, request, job):

        context = {}
        job = Jobs.objects.filter(pk=job)
        if job.count() == 0:
            context['response'] = 'error'
            context['error'] = 'job doesnt exist'
            return Response(data=context)

        user = request.user.profile

        # set relation
        job[0].applicants.add(user)
        job.applicantscount = job.applicantscount + 1

        context['user'] = user
        serializer = self.serializer_class(data=data)
        if serializer.is_valid():
            # if valid save object and send response
            serializer.save()
            # ** turn dictioanries into vars and copy values from serailizer
            context = {**context, **serializer.data.copy()}
            context['response'] = "Success"

            return Response(data=context)


class AppliedJobs(APIView):
    authentication_classes = [IsAuthenticated]
    permission_classes = []
    serializer_class = joblistSerializer

    @swagger_auto_schema(operation_description="headers = {'Authorization': 'Token {token}'} User token")
    def get(self, request):
        context = {}
        if request.user.is_company:
            context['response'] = 'error'
            context['Error'] = 'You are not allowed to access this API'
            return Response(data=context)

        user = request.user.profile
        jobs = Jobs.objects.filter(applicants=user)
        serializer = self.serializer_class(jobs, many=True)
        context['jobs'] = serializer.data
        context['response'] = 'success'
        return Response(data=context)


class CompanyJobs(APIView):
    authentication_classes = []
    permission_classes = []
    serializer_class = joblistSerializer

    @swagger_auto_schema(
        operation_description="Email of the company in the url to get a list of the jobs created by the company")
    def get(self, request, email=None):

        context = {}

        if not email:
            email = request.data.get('email')

        companies = CompanyProfile.objects.filter(user__email=email)

        if companies.count() > 0:
            company = companies[0]

        else:
            context['response'] = 'error'
            context['error_msg'] = 'invalid email'
            return Response(data=context)

        context['company_name'] = company.company_name
        context['company_location'] = company.location
        jobs = Jobs.objects.filter(company=company)
        serializer = self.serializer_class(jobs, many=True)
        # context= {**context,**serializer.data.copy()}
        context['jobs'] = serializer.data
        context['response'] = 'success'
        return Response(data=context)


class HomeScreen(APIView):
    authentication_classes = []
    permission_classes = []
    serializer_class = joblistSerializer

    @swagger_auto_schema(operation_description="Home Screen, in the url ?email=\"\" and ?filter= to filter categories",
                         responses={201: joblistSerializer, 400: 'Bad Request'})
    def get(self, request):
        context = {}
        # retrieve from url

        email = request.GET.get('email')
        filter_category = request.GET.get('category')
        filter_level = request.GET.get('career_level')

        # jobs   = Jobs.objects.all()

        if filter_level and filter_category:

            query = (Q(job_category=filter_category) & Q(career_level=filter_level))


        elif filter_category and not filter_level:

            query = Q(job_category=filter_category)



        elif filter_level and not filter_category:

            query = Q(career_level=filter_level)

        else:

            query = Q()

        account = Account.objects.filter(email=email)

        if account.count() == 0:
            jobs = Jobs.objects.filter(query).order_by(
                '-created_at'
            )

            serializer = self.serializer_class(jobs, many=True)
            context['jobs'] = serializer.data
            context['response'] = 'success'
            return Response(data=context)

        if account:

            user = account[0].profile

        else:
            context['response'] = 'error'
            context['error_msg'] = 'account does not exist'
            return Response(data=context)

        joblist = Jobs.objects.annotate(

            first_query=Case(

                When(Q(job_category__icontains=user.careers_intrests) & Q(career_level__icontains=user.career_level) &
                     Q(job_title__icontains=user.job_title_looking_for)
                     & Q(education_level__icontains=user.education_level) & Q(requirements__icontains=user.skills) & Q(
                    salary__gte=user.min_salary),
                     then=('created_at')),
                default=None
            ),
            second_q=Case(
                When(Q(job_category__icontains=user.careers_intrests) & Q(career_level__icontains=user.career_level) &
                     Q(job_title__icontains=user.job_title_looking_for) & Q(
                    job_title__icontains=user.job_title_looking_for)
                     & Q(education_level__icontains=user.education_level) & Q(requirements__icontains=user.skills) | Q(
                    salary__gte=user.min_salary),
                     then=('created_at')),
                default=None

            ),
            third_q=Case(
                When(
                    Q(job_category__icontains=user.careers_intrests) & Q(career_level__icontains=user.career_level) & Q(
                        job_title__icontains=user.job_title_looking_for)
                    & Q(education_level__icontains=user.education_level) | Q(requirements__icontains=user.skills) | Q(
                        salary__gte=user.min_salary),
                    then=('created_at')),
                default=None

            ), fourth_q=Case(
                When(
                    Q(job_category__icontains=user.careers_intrests) & Q(career_level__icontains=user.career_level) & Q(
                        job_title__icontains=user.job_title_looking_for)
                    | Q(education_level__icontains=user.education_level) | Q(requirements__icontains=user.skills) | Q(
                        salary__gte=user.min_salary),
                    then=('created_at')),
                default=None

            ), fifth_q=Case(
                When(
                    Q(job_category__icontains=user.careers_intrests) & Q(career_level__icontains=user.career_level) | Q(
                        job_title__icontains=user.job_title_looking_for)
                    | Q(education_level__icontains=user.education_level) | Q(requirements__icontains=user.skills) | Q(
                        salary__gte=user.min_salary),
                    then=('created_at')),
                default=None

            ), sixth_q=Case(
                When(
                    Q(job_category__icontains=user.careers_intrests) | Q(career_level__icontains=user.career_level) | Q(
                        job_title__icontains=user.job_title_looking_for)
                    | Q(education_level__icontains=user.education_level) | Q(requirements__icontains=user.skills) | Q(
                        salary__gte=user.min_salary),
                    then=('created_at')),
                default=None

            )

        ).order_by(
            '-first_query', '-second_q', '-third_q', '-fourth_q', '-fifth_q', '-sixth_q',
            '-created_at'
        )

        data = UserJobListSerializer(joblist, many=True).data
        user_skills = str(user.skills).lower().replace(' , ', ',')
        user_skills.replace(' ,', ',')
        user_skills.replace(', ', ',')
        user_skills = user_skills.split(',')
        for job in data:
            score = 0
            job_requirements = job.pop('requirements', '').lower().split(' · ')
            for i in job_requirements:
                for j in user_skills:
                    if fuzz.token_set_ratio(i, j) >= 50:
                        score += 1
                        job['score'] = score

        data = sorted(data, key=lambda k: (k['score'], -k['created_at']))
        context['jobs'] = data
        context['response'] = 'success'
        return Response(data=context)


class users_recommended(APIView):
    authentication_classes = []
    permission_classes = [IsAuthenticated]
    serializer_class = ApplicantSerializer

    @swagger_auto_schema(operation_description=" I want the job id in the url ?job_id=\" ",
                         responses={201: joblistSerializer, 400: 'Bad Request'})
    def get(self, request, job):
        context = {}
        jobs = Jobs.objects.filter(pk=job)
        if job.count() == 0:
            context['response'] = 'error'
            context['error'] = 'job doesnt exist'

            return Response(data=context)

            job = jobs[0]
        q1 = Q(careers_intrests__icontains=job.job_category)
        q2 = Q(career_level__icontains=job.career_level)
        q3 = Q(job_title_looking_for__icontains=job.job_title)
        q4 = Q(education_level__icontains=job.education_level)
        q5 = Q(skills__icontains=job.requirements)
        q6 = Q(min_salary__lte=job.salary)

        userslist = Profile.objects.annotate(first_query=Case(

            When(q1 & q2 & q3 & q4 & q5 & q6)
        ),
            second_q=Case(
                When(q1 & q2 & q3 & q4 & q5 | q6)

            ),
            third_q=Case(
                When(q1 & q2 & q3 & q4 | q5 | q6)
            ), fourth_q=Case(
                When(q1 & q2 & q3 | q4 | q5 | q6))
            ,
            fifth_q=Case(
                When(q1 & q2 | q3 | q4 | q5 | q6))

            , sixth_q=Case(
                When(q1 | q2 | q3 | q4 | q5 | q6)
            )
        ).order_by(
            '-first_query', '-second_q', '-third_q', '-fourth_q', '-fifth_q',
            '-sixth_q')

        serializer = self.serializer_class(userslist, many=True)
        context['users'] = serializer.data
        context['response'] = 'success'
        return Response(data=context)


class SendMail(APIView):
    authentication_classes = []
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(operation_description="headers = {'Authorization': 'Token {token}'} Company token",
                         request_body=openapi.Schema(
                             type=openapi.TYPE_OBJECT,
                             properties={
                                 'job': openapi.Schema(type=openapi.TYPE_STRING, description=' job primary key'),
                                 'email': openapi.Schema(type=openapi.TYPE_STRING, description=' user email'),
                                 'operation': openapi.Schema(type=openapi.TYPE_STRING,
                                                             description=' send it as (Accepted or short or reject'),

                             }),
                         responses={201: JobSerializer, 400: 'Bad Request'})
    def post(self, request):

        email = request.data.get('email')
        jobpk = request.data.get('job')
        job = Jobs.objects.filter(pk=jobpk)
        account = Account.objects.filter(email=email)
        company = request.user.companyprofile.company_name
        operation = request.data.get('operation')

        if operation == 'Accepted':

            body = f'Congratulations {account.firstname} !, your application have been accepted in the {job.job_title} job from company' \
                   f' {company} and you will be contacted for the next step soon by them and remember keep workin  ' \
                   f'From Work-in Team ! '
            subject = f'{job.job_title} at {company} application status'
            SendMail(subject, body, email).start()

        elif operation == 'short':
            body = f'Congratulations {account.firstname} !, your application have been shortlisted in the {job.job_title} job from company' \
                   f' {company} and you will be contacted for the next step soon by them, and remember keep workin' \
                   f'From Work-in Team ! '
            subject = f'{job.job_title} at {company} application status'
            SendMail(subject, body, email).start()

        elif operation == 'reject':
            body = f'hello {account.firstname} ,we are sorry to inform you that  your application have been rejected in the {job.job_title} job from company' \
                   f' {company} and we hope we find your next job soon in work-in!  '
            subject = f'{job.job_title} at {company} application status'
            SendMail(subject, body, email).start()

























