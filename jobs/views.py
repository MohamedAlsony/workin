import re
from thefuzz import fuzz, process
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
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.parsers import FileUploadParser, JSONParser, MultiPartParser, DataAndFiles, BaseParser
from jobs.models import Jobs, Applicant
from jobs.serializers import *
from mysite.tasks import SendOperationMail

class JobCreation(APIView):
    authentication_classes = [TokenAuthentication, ]
    permission_classes     = [IsAuthenticated]
    serializer_class       = JobSerializer

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
            job =   serializer.save()
            # ** turn dictioanries into vars and copy values from serailizer
            context = {**context, **serializer.data.copy()}
            context['response'] = "Success"

            career_interest = job.job_category
            if 'Development' in job.job_category or 'Engineering' in job.job_category:
                career_interest = 'Software Engineering'
            elif 'Design' in job.job_category:
                career_interest = 'Design'
            query  = (Q(careers_intrests=career_interest) & Q(career_level=job.career_level))
            users  = Profile.objects.filter(query)
            print(users)

            for user in users:

                account = user.user
                email = account.email
                companyname=request.user.companyprofile.company_name
                # body = f'Hey {account.firstname} !, be the first one that applies to  {job.job_title} job from company {companyname} as the job matches your profile! ' \
                #        f' and remember keep workin' \
                #        f'From Work-in Team ! '

                subject = f'Check the latest job from workin'
                SendOperationMail(subject=subject, operation='recommend', email=email, account=account,job=job, companyname=companyname).start()


            account = request.user
            email = request.user.email
            companyname=request.user.companyprofile.company_name
            # body = f'Hey {self.account.firstname}
            # You posted {self.job.job_title} position as  company {companyname}
            # We will notify you when someone apply and we will recommend to you suitable applicant
            # check  the job page for recommended applicants! ' \
            # Happy hunting
            # From Work-in Team"

            subject = f'Job posted on Workin!'
            SendOperationMail(subject=subject, operation='JobPosted', email=email, account=account,job=job, companyname=companyname).start()


            return Response(data=context)



        else :

            context = serializer.errors.copy()
            context['response'] = 'error'
            return Response(data=context)

    @swagger_auto_schema(operation_description="headers = {'Authorization': 'Token {token}'}  Company token",
                         request_body=openapi.Schema(
                             type=openapi.TYPE_OBJECT,
                             properties={
                                 'Same data of the response example': openapi.Schema(type=openapi.TYPE_STRING,
                                                                                     description='7abeby'),
                             }),
                         responses={200: serializer_class, 400: 'Bad Request'})
    def put(self, request, *args, **kwargs):

        context = {}
        if not request.user.is_company:
            context['response'] = 'error'
            context['error'] = 'you are not allowed to access this API'

            return Response(data=context)


        data = request.data.copy()
        job = Jobs.objects.filter(id=data.get('job_id')).first()
        if not job:
            context['response'] = 'error'
            context['error'] = 'job not found.'
            return Response(context)


        # set relation
        serializer = self.serializer_class(job, data=data, partial=True)

        if serializer.is_valid():
            # if valid save object and send response
            job = serializer.save()
            # ** turn dictioanries into vars and copy values from serailizer
            context = {**context, **serializer.data.copy()}
            context['response'] = "Success"
            return Response(context)
        context['response'] = 'error'
        context.update(serializer.errors)
        return Response(context)


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

        # bos aleha


        #if not job_detail.salary is None :
            #context['salary'] = "Confidential"

        serializer = self.serializer_class(job_detail)
        context = {**context, **serializer.data.copy()}
        context['response'] = 'success'
        return Response(data=context)


class CompanyJobDetail(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes     = [IsAuthenticated]
    serializer_class       = CompanyJobSerializer

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
        #if not job.salary:
            #context['salary'] = "Confidential"
        context['response'] = 'success'
        return Response(data=context)


class JobApply(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes     = [IsAuthenticated]
    serializer_class       = JobSerializer

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
        #check if applied before
        job=job[0]
        if job.applicants.filter(profile__user_id=request.user.id):
            context['response'] = 'error'
            context['error'] = ' you applied to this job before'
            return Response(data=context)


        # set relation

        applicant = Applicant(profile=user, job=job)
        applicant.save()
        job.applicants.add(applicant)
        job.applicantscount = job.applicantscount + 1
        job.save()

        context['user'] = user.user.email
        context['response'] = "Success"


        from mysite.tasks import SendMail
        account = user.user
        email = account.email


        subject = f'Job Application status'
        SendOperationMail( subject=subject, email=email,job=job,account=account,companyname=job.company.company_name,operation='UserApplied').start()


        account   = request.user
        email     = job.company.user.email
        # body = f'Hey {companyUser.firstname} ! , representive  of  {job.company.company_name} company, Your  post on {job.job_title} is being viewed and applied to! check the recent applied users in your work-in profile! .' \
        #            f'and remember keep Hiring on work-in!',\
        #         f'From Work-in Team ! '
        # subject = f'Job post status!'
        SendOperationMail( subject=subject, email=email,job=job,account=account,companyname=job.company.company_name,operation='Applied').start()







        return Response(data=context)




class AppliedJobs(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes     = [IsAuthenticated]
    serializer_class       = joblistSerializer

    @swagger_auto_schema(operation_description="headers = {'Authorization': 'Token {token}'} User token")
    def get(self, request):
        context = {}
        if request.user.is_company:
            context['response'] = 'error'
            context['Error'] = 'You are not allowed to access this API'
            return Response(data=context)

        user = request.user.profile
        jobs = Jobs.objects.filter(applicants__profile=user)
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

class Search(APIView):
    authentication_classes = []
    permission_classes     = []
    serializer_class       = joblistSerializer

    @swagger_auto_schema(operation_description="search bar , search in the url ..",
                         responses={201: joblistSerializer, 400: 'Bad Request'})

    def get(self, request,search):
        reg = r'[a-zA-Z](?:[a-z]+|[A-Z]*(?=[A-Z]|$))'

        search  = re.findall(reg, str(search))
        print('zzz')

        print(search)

        context = {}
        joblist = []

        print(joblist)
        for i in search:
            print(search)
            query1 = (Q(job_title__icontains = i))
            jobs  = Jobs.objects.select_related('company__user').filter(query1)
            joblist+=jobs

        for i in search:
            print(search)
            query = (Q(requirements__icontains = i) &~ Q(job_title__icontains = i))
            jobs  = Jobs.objects.select_related('company__user').filter(query)
            joblist+=jobs




        print(joblist)
        serializer = self.serializer_class(joblist, many=True)
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


            query = (Q(job_category=filter_category) & Q(career_level__icontains=filter_level))


        elif filter_category and not filter_level:

            query = Q(job_category__icontains=filter_category)

        elif filter_level and not filter_category:

            query = Q(career_level__icontains=filter_level)

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

        if filter_level and filter_category:

            query = (Q(job_category=filter_category) & Q(career_level__icontains=filter_level))


        elif filter_category and not filter_level:

            query = Q(job_category__icontains=filter_category)

        elif filter_level and not filter_category:

            query = Q(career_level__icontains=filter_level)

        else:

            query = Q()

        joblist     = Jobs.objects.select_related('company__user').filter(query)
        data        = UserJobListSerializer(joblist, many=True).data
        career_interest = user.careers_intrests
        if career_interest == 'Software Engineering':
            career_interest = 'IT/Software Development'
        elif career_interest == 'Architecture':
            career_interest = 'Engineering'
        for i in data:
            print('extra_data')
            print(i.get('job_title'))
            # check careers_intrests matching
            careers_intrests_match = str(user.careers_intrests).lower() in str(i.get('job_category','')).lower()
            #check education_level matching
            education_level_match = str(user.education_level).lower() in str(i.get('education_level','')).lower()
            #check career_level matching
            career_level_match = str(user.career_level).lower() in str(i.get('career_level','')).lower()
            #calculate the summition
            score = career_level_match+careers_intrests_match+education_level_match
            if score==3:
                i['score'] = 90
            elif score==2:
                i['score'] = 40
            else:
                i['score'] = 15

        # if no filter  defined in url adding the excluded objects
        if not (filter_level or  filter_category) :
            joblist_excluded = Jobs.objects.select_related('company__user').exclude(id__in = [i.id for i in joblist])
            extra_data = UserJobListSerializer(joblist_excluded, many=True).data

            data += extra_data


            for i in data:
                i['score'] = i.get('score', 0)
        # regular expression to split normal words or camel case words from string
        reg = r'[a-zA-Z](?:[a-z]+|[A-Z]*(?=[A-Z]|$))'
        #apply the regular expression on the user_skills string
        user_skills = re.findall(reg, str(user.skills))
        user_job_titles = re.findall(reg , str(user.job_title_looking_for))
        #define words that will spoil the score to omit them from tthe word list
        skipped_words = {'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', 'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she', 'her', 'hers', 'herself', 'it', 'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves', 'what', 'which', 'who', 'whom', 'this', 'that', 'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until', 'while', 'of', 'at', 'by', 'for', 'with', 'about', 'against', 'between', 'into', 'through', 'during', 'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again', 'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'can', 'will', 'just', 'don', 'should', 'now', 'level', 'time', 'a', 'an', 'the'}
        for i in user_skills[:]:
            if str(i).lower() in skipped_words:
                user_skills.remove(i)

        for i in user_job_titles[:]:
            if str(i).lower() in skipped_words:
                user_job_titles.remove(i)


        weight = 5
        for job in data:
            job_data = re.findall(reg, job.get('job_title', '') + job.get('description', '') + job.get('requirements', ''))
            for i in user_skills:
                print('skills')


                #check wheather user skill match the job
                if list(process.extractWithoutOrder(i,job_data , score_cutoff=75, scorer=fuzz.token_set_ratio)):
                    print(i,list(process.extractWithoutOrder(i,job_data , score_cutoff=75, scorer=fuzz.token_set_ratio))[0])
                    print(job.get('job_title'))
                    job['score'] = job.get('score', 0) + 5



            for i in user_job_titles:
                print('title')

                #check wheather title match the job
                if list(process.extractWithoutOrder(i, job_data, score_cutoff=75, scorer=fuzz.token_set_ratio)):
                    print(i, list(process.extractWithoutOrder(i, job_data, score_cutoff=75, scorer=fuzz.token_set_ratio))[0])
                    print(job.get('job_title'))
                    job['score'] = job.get('score', 0) + 50 * weight
                    weight = max(1, weight-1)
            weight = 5
        #sort jobs based on score and date
        data = sorted(data, key=lambda k : (k['score'], k['created_at']), reverse=True)



        context['jobs'] = data
        print(data)
        context['response'] = 'success'
        return Response(data=context)


class users_recommended(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes     = [IsAuthenticated]
    serializer_class       = RecmmondedUsersSerializer

    @swagger_auto_schema(operation_description=" I want the job id in the url ?job_id=\" ",
                         responses={201: joblistSerializer, 400: 'Bad Request'})
    def get(self, request, job):
        context = {}

        job = Jobs.objects.filter(pk=job)
        if job.count() == 0:
         context['response'] = 'error'
         context['error'] = 'job doesnt exist'
         return Response(data=context)

        job = job.first()

        career_interest = job.job_category
        if 'Development' in job.job_category or 'Engineering' in job.job_category:
            career_interest = 'Software Engineering'
        elif 'Design' in job.job_category:
            career_interest = 'Design'

        query = ( Q(careers_intrests__icontains=career_interest) & Q(career_level__icontains=job.career_level) & Q(education_level__icontains=job.education_level)&
                ( Q(careers_intrests__icontains=career_interest) & Q(career_level__icontains=job.career_level) | Q(education_level__icontains=job.education_level))&
                ( Q(careers_intrests__icontains=career_interest) | Q(career_level__icontains=job.career_level) | Q(education_level__icontains=job.education_level)) & Q(user__is_company=False) )


        UsersList  = Profile.objects.select_related('user').filter(query).exclude(pk__in= [i.profile.pk for i in job.applicants.all()])
        print(UsersList)

        data =  self.serializer_class(UsersList, many=True).data

        for i in data:
            i['score'] = 40



        reg = r'[a-zA-Z](?:[a-z]+|[A-Z]*(?=[A-Z]|$))'
        job_data = re.findall(reg, str(job.job_title + job.description +job.requirements))

        skipped_words = {'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', 'your', 'yours', 'yourself', 'yourselves', 'he', 'him',
                         'his', 'himself', 'she', 'her', 'hers', 'herself', 'it', 'its', 'itself', 'they', 'them', 'their', 'theirs',
                         'themselves', 'what', 'which', 'who', 'whom', 'this', 'that', 'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be', 'been',
                         'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until', 'while',
                         'of', 'at', 'by', 'for', 'with', 'about', 'against', 'between', 'into', 'through', 'during', 'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again', 'further', 'then', 'once',
                         'here', 'there', 'when', 'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'can', 'will', 'just', 'don', 'should', 'now', 'level', 'time', 'a', 'an', 'the'}
        for i in job_data[:]:
           if str(i).lower() in skipped_words:
              job_data.remove(i)

        weight = 5
        for user in data:

            user_job    = re.findall(reg, user.get('job_title_looking_for', ''))
            user_skills = re.findall(reg, user.get('skills', ''))

            for i in user_skills:
                print('user_data')


                if list(process.extractWithoutOrder(i,job_data , score_cutoff=75, scorer=fuzz.token_set_ratio)):
                    print(i)
                    print(user_job)
                    user['score'] = user.get('score', 0) + 5



            for i in user_job:
                print(user_skills)

                if list(process.extractWithoutOrder(i, job_data, score_cutoff=75, scorer=fuzz.token_set_ratio)):

                    print(i)
                    print(user_skills)
                    user['score'] = user.get('score', 0) + 50 * weight
                    weight = max(0, weight-1)

            weight = 5
        data = sorted(list(filter(lambda i: i.get('score', 0) >= 50, data)), key=lambda k : (k['score']),reverse =True)



        context.update(JobSerializer(job).data)
        context['users']    = data
        context['response'] = 'success'

        return Response(data=context)

class SendMail(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes     = [IsAuthenticated]

    @swagger_auto_schema(operation_description="headers = {'Authorization': 'Token {token}'} Company token",
                         request_body=openapi.Schema(
                             type=openapi.TYPE_OBJECT,
                             properties={
                                 'job': openapi.Schema(type=openapi.TYPE_STRING, description=' job primary key'),
                                 'email': openapi.Schema(type=openapi.TYPE_STRING, description=' user email'),
                                 'operation': openapi.Schema(type=openapi.TYPE_STRING,
                                                             description=' send it as (Accepted or '
                                                                         '' 'short or reject or invite'),
                             }),
                         responses={201: JobSerializer, 400: 'Bad Request'})

    def post(self, request):
        context={}
        email = request.data.get('email')
        jobpk = request.data.get('job')
        job = Jobs.objects.filter(pk=jobpk).first()
        account = Account.objects.filter(email=email).first()
        company = request.user.companyprofile.company_name
        operation = request.data.get('operation')

        from mysite.tasks import SendMail

        if operation == 'Accepted':

            # body = f'Congratulations {account.firstname} !, your application have been accepted in the {job.job_title} job from company' \
            #        f' {company} and you will be contacted for the next step soon by them and remember keep workin  ' \
            #        f'From Work-in Team ! '
            subject = f'{job.job_title} at {company} application status'
            SendOperationMail(subject=subject, operation='Accepted', email=email, account=account,job=job, companyname=company).start()
            context['operation'] = operation+' is sent'
            context["response"] = 'success'

        elif operation == 'short':
            body = f'Congratulations {account.firstname} !, your application have been shortlisted in the {job.job_title} job from company' \
                   f' {company} and you will be contacted for the next step soon by them, and remember keep workin' \
                   f'From Work-in Team ! '
            subject = f'{job.job_title} at {company} application status'
            SendOperationMail(subject=subject, operation='short', email=email, account=account,job=job, companyname=company).start()
            context['operation'] = operation+' is sent'
            context["response"] = 'success'


        elif operation == 'reject':
            # body = f'hello {account.firstname} ,we are sorry to inform you that  your application have been rejected in the {job.job_title} job from company' \
            #        f' {company} and we hope we find your next job soon in work-in!  '
            subject = f'{job.job_title} at {company} application status'
            SendOperationMail(subject=subject, operation='reject', email=email, account=account,job=job, companyname=company).start()
            context['operation'] = operation+' is sent'
            context["response"] = 'success'


        elif  operation =='invite':
                #body = f'Congratulations {account.firstname} your profile is being noticed! ;) {company} is inviting you to check  ' \
                       #f' {job.job_title} position in their profile and see if its in your intrest to apply on it!'

                subject = f' {company}  invitation for {job.job_title } position'
                #SendMail(subject,body, email).start()
                SendOperationMail(subject=subject, operation='invite', email=email, account=account,job=job, companyname=company).start()
                context['operation'] = operation+' is sent'
                context["response"] = 'success'

        else:
            context['response'] = ['error']
            context['error']    = ['err']


        if operation== 'reject' or operation == 'Accepted':
            applicant = Applicant.objects.filter(job_id = job.id, profile__user_id=account.id)
            applicant.delete()
            job.applicantscount = max(0 , job.applicantscount-1)
            job.save()
        return Response(data = context)






