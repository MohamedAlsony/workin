from account.models import Account
from django.db import models
#from django_mysql.models import ListCharField

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token
import re
from cloudinary.models import CloudinaryField
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator




#remove class MyAccountManager(BaseUserManager):

#remove class CompanyAccount(AbstractBaseUser):





class CompanyProfile(models.Model):
    #review = models.OneToOneField(Account,on_delete=models.CASCADE,primary_key=True,)

    #Lists of choices
    industries         =  [("T","Tech"),("ARCH","Architecture")
		,("TR","Translation"),("DES","Design"),("MA","Media and Advertising"),("ME","Medicine")]

    company_types      =  [("PRV","Private company"),("PUB","Public Company"),("NPO","Non Profit Organization")]

    company_sizes      = [("SB","Small Business"),("ME","Mid Market enterprise"),("EN","Enterprise")]

    #Data

    #make company related to Account model

    user               = models.OneToOneField(Account,on_delete=models.CASCADE,primary_key=True,)
    #image attribute

    size_of_company    = models.CharField(max_length=25,null = True, default='')
    company_name       = models.CharField(max_length=25,null = True, default='')
    company_info       = models.CharField(max_length=1500,null = True, default='')


    company_industries = models.CharField(max_length=25,default='T',null = True)
    company_type       = models.CharField(max_length=25,default='Private',null = True)
    mobile_number      = models.CharField(max_length=13,null=True, default='')
    job_title          = models.CharField(max_length=25,null=True, default='hr')
    no_of_employees    = models.CharField(max_length=9,null=True, default='28')
    isInternational    = models.BooleanField(null=True, default=False)
    headquarters       = models.CharField(max_length=30,null=True, default='')
    founded_at         = models.PositiveSmallIntegerField(validators=[MinValueValidator(1800), MaxValueValidator(2023)], blank=True, null=True, default=2009)
    website            = models.CharField(max_length=100,null=True, default='')
    location           = models.CharField(max_length=50,null=True, default='')
    specialities = models.CharField(max_length=500,null=True, default='')
    def __str__(self):
        return self.company_name



    """ #Multiple locations??
    locations = ListCharField(
        base_field=CharField(max_length=10),
        size=6,
        max_length=(6 * 11)  # 6 * 10 character nominals, plus commas
    )
"""
"""
    def clean(self):
        if not bool(re.fullmatch('[A-Za-z]{2,25}( [A-Za-z]{2,25})?',self.job_title)):
             raise ValidationError({'job_title': "names must not contain digits!"})



        if not bool(re.fullmatch('/^\d[\d+]*$',self.no_of_employees)):
             raise ValidationError({'no_of_employees': "only numbers are allowed!"})



        if not bool(re.fullmatch('/^\d[\d+]*$',self.mobile_number)):
             raise ValidationError({'mobile_number': "only numbers are allowed!"})

"""


class Review(models.Model) :

    rating  =  models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], blank=True, null=True, default=4)
    review  =  models.CharField(max_length=500,null=True, default='')
    user    =  models.CharField(max_length=25, default='')
    date    =  models.DateField(auto_now_add=True)
    company = models.ForeignKey(CompanyProfile,on_delete=models.CASCADE, blank=True)




