from rest_framework   import serializers
from companies.models import Review
from account.models   import Account
from companies.models import CompanyProfile


class CompanyRegistrationSerializer(serializers.ModelSerializer):

	class Meta:
		model = Account
		fields = ['email', 'firstname', 'lastname', 'password', 'is_staff',  'verified','is_company']
		extra_kwargs = {
				'password': {'write_only': True, 'min_length': 8, 'max_length': 50},
		}


	def	save(self) :

		account = Account(
		email=self.validated_data['email'], is_company= True)
		password = self.validated_data['password']

		account.set_password(password)
		account.save()
		return account

class CompanyProfileSerializer(serializers.ModelSerializer):
	logo = serializers.SerializerMethodField()

	class Meta:
		model = CompanyProfile
		fields = '__all__'

	def get_logo(self, company_profile):
		if company_profile.user.file:
			return company_profile.user.file.url
		return ''


class LogoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ['file']

class ReviewSereializier(serializers.ModelSerializer):
	class Meta :
		model   = Review
		fields  = '__all__'



