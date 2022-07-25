from django.db import models
from companies.models import CompanyProfile
from account.models import Profile

class Jobs(models.Model):

    company                 =  models.ForeignKey(CompanyProfile,on_delete=models.CASCADE)
    job_title               =  models.CharField(max_length=100,default="junior")
    job_category            =  models.CharField(max_length=50,default="IT")
    job_type                =  models.CharField(max_length=20,default="fulltime")
    #education_level_choices =  [("ST","Student"),("BCH","Bachelor"),("UG","UnderGrad"),("MST","Masters"),("PHD","PHD")]
    description             =  models.CharField(max_length=1000, default='')
    requirements            =  models.CharField(max_length=1000, default='')
    education_level         =  models.CharField(max_length=20, default='')
    experience              =  models.CharField(max_length=10, default='')
    career_level            =  models.CharField(max_length=20,default="Junior")
    salary                  =  models.CharField(max_length=20,null=True, blank=True)
    isConfidential          =  models.BooleanField(default=True)
    applicants              =  models.ManyToManyField('Applicant',blank=True)
    created_at              =  models.DateTimeField(auto_now_add=True,null=True)
    applicantscount         = models.PositiveSmallIntegerField(default=0)

    def save(self, *args, **kwargs):
        try:
            int(self.salary)
            self.salary+= 'EGP/Month'
        except TypeError:
            self.salary = 'Confidential salary'
        except ValueError:
            pass
        super(Jobs, self).save(*args, **kwargs)

    def __str__(self):
        return str(self.id) +  ' ' + self.job_title

class Applicant(models.Model):
    profile = models.ForeignKey(Profile, null=True, blank=True, on_delete=models.CASCADE)
    job = models.ForeignKey(Jobs, null=True, blank=True,on_delete=models.CASCADE)
    applied_at = models.DateTimeField(auto_now_add=True)





