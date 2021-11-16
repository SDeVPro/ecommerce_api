from django.contrib.auth.backends import AllowAllUsersModelBackend
from django.contrib.auth.models import User 
from django.core.exceptions import PermissionDenied

class EmailBackend(AllowAllUsersModelBackend):
    def authenticate(self,request,username=None,password=None,**kwargs):
        if username is None:
            username = kwargs.get("username")

        try:
            if (username[0]=="+"):#+99891
                user = User.objects.get(profile__phone_number=username)    
            else:
                user = User.objects.get(email=username)
        except User.DoesNotExist:
            raise PermissionDenied("This User doesn't exist.")
        else:
            if user.check_password(password) and self.user_can_authenticate(user):
                return user 
                


