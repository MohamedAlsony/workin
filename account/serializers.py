from rest_framework import serializers

from account.models import Account,Profile
from companies.models import CompanyProfile


class RegistrationSerializer(serializers.ModelSerializer):

	class Meta:
		model = Account
		fields = ['email', 'firstname', 'lastname', 'password', 'is_staff',  'verified',]
		extra_kwargs = {
				'password': {'write_only': True, 'min_length': 8, 'max_length': 50},
		}


	def	save(self) :

		account = Account(
			email=self.validated_data['email'],
			firstname=self.validated_data['firstname'],
			lastname=self.validated_data['lastname'],
				)
		password = self.validated_data['password']
		account.set_password(password)
		account.save()
		return account

class UserProfileSerializer(serializers.ModelSerializer):
	picture = serializers.SerializerMethodField()
	class Meta:
		model =	 Profile
		fields = '__all__'

	def get_picture(self, profile):
		if profile.picture:
			return profile.picture.url
		return ''


class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ['file']

class PictureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['picture']



