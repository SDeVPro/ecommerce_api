from django.contrib.auth import get_user_model,authenticate
from django.conf import settings 
from django.contrib.auth.forms import SetPasswordForm
from rest_framework import serializers,exceptions
from phonenumber_field.serializerfields import PhoneNumberField
from rest_auth.registration.serializers import RegisterSerializer 
from rest_framework.validators import UniqueValidator
from rest_framework.exceptions import ValidationError
from drf_extra_fields.fields import Base64ImageField 
from django.contrib.auth.models import Permission
from django.utils.translation import ugettext_lazy as _ 
from allauth.account.models import EmailAddress 
from .models import Profile,Address,SMSVerification,DeactivateUser,NationalIDImage

UserModel = get_user_model()

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=False,allow_blank=True)
    password = serializers.CharField(style={"input_type":"password"})
    def authenticate(self,**kwargs):
        return authenticate(self.context["request"],**kwargs)
    
    def _validate_email(self,email,password):
        user = None 
        if email and password:
            user = self.authenticate(email=email,password=password)
        else:
            msg = _('Must include "email" and "password".')
            raise exceptions.ValidationError(msg)
        return user 
    def _validate_username(self,username,password):
        user = None 
        if username and password:
            user = self.authenticate(username=username,password=password)
        else:
            msg = _('Must include "username or "email" or "phone number" and "password".')
            raise exceptions.ValidationError(msg)
        return user 
    def _validate_username_email(self,username,email,password):
        user = None 
        if email and password:
            user = self.authenticate(email=email,password=password)
        elif username and password:
            user = self.authenticate(username=username,password=password)
        else:
            msg = _('Mist include either "username" or "email" or "phone number" and "password".')
            raise exceptions.ValidationError(msg)
        return user 
    def validate(self,attrs):
        username = attrs.get("username")
        password = attrs.get("password")
        user = None 
        if "allauth" in settings.INSTALLED_APPS:
            from allauth.account import app_settings
            if (app_settings.AUTHENTICATION_METHOD == app_settings.AuthenticationMethod.EMAIL):
                user = self._validate_email(email,password)
            elif (app_settings.AUTHENTICATION_METHOD == app_settings.AuthenticationMethod.USERNAME):
                user = self._validate_username(username,password)
            else:
                user = self._validate_username_email(username,email,password)
        else:
            if username:
                user = self._validate_username_email(username,"",password)
        if user:
            if not user.is_active:
                msg = _("user account is inactive.")
                raise  exceptions.ValidationError(msg)
        else:
            msg = _("please check your username or email or phone number or password.")
            raise exceptions.ValidationError(msg)
        if "rest_auth.registration" in settings.INSTALLED_APPS:
            from allauth.account import app_settings 
            if (app_settings.EMAIL_VERIFICATION == app_settings.EmailVerificationMethod.MANDATORY):
                try:
                    email_addres = user.emailaddress_set.get(email=user.email)
                except EmailAddress.DoesNotExist:
                    raise serializers.ValidationError(
                        _("This account don't have E-mail address!so that you can't login.")
                    )
                if not email_addres.verified:
                    raise serializers.ValidationError(_("E-mail is not verified."))
            try:
                phone_number = user.sms 
            except SMSVerification.DoesNotExist:
                raise serializers.ValidationError(
                    _("This account don't have Phone Number!")
                )
            if not phone_number.verified:
                raise serializers.ValidationError(_("Phone Number is not verified."))
            attrs["user"]=user 
            return attrs 
