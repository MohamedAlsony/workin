import json
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase
from account.serializers import RegistrationSerializer
from account.models import Account
# Create your tests here.

class RegistirationTestCase(APITestCase):
    def setUp(self):

        self.email=Account.objects.create(email='test@localhost.app')
        self.email.set_password('some_strng_pass')
        self.email.save()


    def test_company_registiration(self):
        data={"email":"tesst@localhost.app",
          "password":"some_strnng_pass"}

        response = self.client.post("/api/company/register/",data)
        print("registiration one response",response.data)

        self.assertEqual(response.status_code, 200)


    def test_company_registiration_two(self):

        data={"email":"test@localhost.app","firstname":"test",
          "lastname":"case","company_name":"testC","job_title":"TR",
        "mobile_number":"012","company_industries":"TR","size_of_company":"SB",
          "is_staff":"false"
            ,"verified":"false","is_company":"true"}


        response = self.client.post("/api/company/register/2",data)
        print("registiration 2 response:",response.data)


        self.assertEqual(response.status_code, 200)

    def test_company_login(self):

        data={"email":"test@localhost.app",
          "password":"some_strng_pass"}

        response = self.client.post("/api/company/login/",data)

        self.assertEqual(response.status_code, 200)
        print("logged in********************************")
        print("Login response :",response.data)


    def test_companyprofile_setup(self):

        data={"email":"test@localhost.app","website":"www.company.com","founded_at":"",
              "Location":"23 st ahmad","headquarters":"place","company_type":"PRV",
              "company_info":"wqerwffijdnfijdsfoudhfoudbsofubsdofbsdofb"
}


        response = self.client.post("/api/company/Profile_setup/", data)
        print("profile setup response:",response.data)


        self.assertEqual(response.status_code, 200)
