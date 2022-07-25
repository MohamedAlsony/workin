from rest_framework import serializers
from django.contrib.humanize.templatetags.humanize import naturaltime
from django.utils import timezone
from account.models import Profile
from jobs.models import Jobs, Applicant

class ApplicantSerializer(serializers.ModelSerializer):
    email     = serializers.CharField(source='profile.user.email')
    firstname = serializers.CharField(source='profile.user.firstname')
    lastname  = serializers.CharField(source='profile.user.lastname')
    job_title_looking_for  = serializers.CharField(source='profile.job_title_looking_for')
    picture = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()

    class Meta:
        model = Applicant
        fields = ('email', 'firstname', 'lastname', 'applied_at', 'picture', 'location', 'job_title_looking_for')

    def get_picture(self, applicant):
        if applicant.profile.picture:
            return applicant.profile.picture.url
        return ''

    def get_location(self, applicant):
        if applicant.profile.country and applicant.profile.city:
            return str(applicant.profile.country + ', ' + applicant.profile.city).replace(',,', ',')
        return ''

class RecmmondedUsersSerializer(serializers.ModelSerializer):
    email     = serializers.CharField(source='user.email')
    firstname = serializers.CharField(source='user.firstname')
    lastname  = serializers.CharField(source='user.lastname')
    picture = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = ('email', 'firstname', 'lastname',  'picture', 'location', 'job_title_looking_for')

    def get_picture(self, Profile):
        if Profile.picture:
            return Profile.picture.url
        return ''

    def get_location(self, Profile):
        if Profile.country and Profile.city:
            return str(Profile.country + ', ' + Profile.city).replace(',,', ',')
        return ''

class CompanyJobSerializer(serializers.ModelSerializer):
    applicants = ApplicantSerializer(many=True, read_only=True)
    logo = serializers.SerializerMethodField()
    company_email     = serializers.CharField(source='company.user.email', required=False)
    class Meta:
        model = Jobs
        exclude = ['requirements', 'description']
        read_only_fields = ['company_email']
    def get_logo(self, job):
        if job.company.user.file:
            return job.company.user.file.url
        return ''



class JobSerializer(serializers.ModelSerializer):
    logo = serializers.SerializerMethodField()
    company_email     = serializers.CharField(source='company.user.email', required=False)
    class Meta:
        model = Jobs
        exclude = ['applicants','applicantscount']
        read_only_fields = ['company_email']

    def get_logo(self, job):
        if job.company.user.file:
            return job.company.user.file.url
        return ''




class joblistSerializer(serializers.ModelSerializer):

    logo     = serializers.SerializerMethodField()
    name     = serializers.CharField(source='company.company_name')
    company_email     = serializers.CharField(source='company.user.email')
    location = serializers.CharField(source='company.location')




    class Meta:
        model = Jobs
        fields = ('logo', 'created_at', 'applicantscount', 'company', 'name','location','id', 'job_type','job_title','company_email')

    def get_logo(self, job):
        if job.company.user.file:
            return job.company.user.file.url
        return ''



class UserJobListSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='company.company_name')
    company_email = serializers.CharField(source='company.user.email')
    location = serializers.CharField(source='company.location')
    logo = serializers.SerializerMethodField()
    class Meta:
        model = Jobs
        fields = ('logo', 'created_at', 'applicantscount', 'company', 'id', 'job_type','job_title', 'job_category', 'career_level', 'education_level', 'requirements', 'description', 'name','location', 'company_email')

    def get_logo(self, job):
        if job.company.user.file:
            return job.company.user.file.url
        return ''






