import socket
import datetime
from django.conf import settings 
from django.core.cache import DEFAULT_CACHE_ALIAS, caches,cache
from django.http import response
from django.utils.cache import get_cache_key,get_max_age,has_vary_header,learn_cache_key,patch_response_headers
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.models import AnonymousUser,User 

class ActivateUserMiddleware(MiddlewareMixin):
    def process_request(self,request):
        if request.user.is_authenticated:
            now = datetime.datetime.now(datetime.timezone.utc)
            cache.set(
                f"seen_{request.user.username}",now,settings.USER_LASTSEEN_TIMEOUT
            )
        return None 
class GooglebotMiddleware(object):
    def process_request(self,request):
        request.is_googlebot = False 
        if request.user == AnonymousUser():
            if request.META.get("HTTP_USER_AGENT"):#browser 
                if "Googlebot" in request.META["HTTP_USER_AGENT"]:
                    try:
                        remote_ip = request.META["META_ADDR"]
                        hostname = socket.gethostbyaddr(remote_ip)[0]
                        if hostname.endswith("googlebot.com"):
                            request.user, created = User.objects.get_or_create(
                                username = "googlebot"
                            )
                            request.is_googlebot = True
                        else:
                            request.is_googlebot = False 
                    except Exception:
                        pass 
        return None

class UpdateCacheMiddleware(MiddlewareMixin):
    def __init__(self,get_response=None):
        self.cache_timeout = settings.CACHE_MIDDLEWARE_SECONDS 
        self.key_prefix = settings.CACHE_MIDDLEWARE_KEY_PREFIX 
        self.cache_alias = settings.CACEH_MIDDLEWARE_ALIAS 
        self.cache = caches[self.cache_alias]
        self.get_response = get_response 
    def _should_update_cache(self,request,response):
        return  hasattr(request,"_cache_update_cache") and request._cache_update_cache 
    def process_response(self,request,response):
        if not self._should_update_cache(request,response):
            return response
        if response.streaming or response.status_code not in (200,304):
            return response 
        if (not request.COOKIES and response.cookies and has_vary_header(response,"Cookie")):
            return response 
        timeout = get_max_age(response)
        if timeout is None:
            timeout = self.cache_timeout
        elif timeout == 0:
            return response 
        patch_response_headers(response,timeout)
        if timeout and response.status_code == 200:
            cache_key = learn_cache_key(
                request,response,timeout,self.key_prefix,cache=self.cache
            )
            if hasattr(response,"render") and callable(response.render):
                response.add_post_render_callback(
                    lambda r: self.cache.set(cache_key,r,timeout)
                )
            else:
                self.cache.set(cache_key,response,timeout)
        return response
class FetchFromCacheMiddleware(MiddlewareMixin):
    def __init__(self,get_response=None):
        self.key_prefix = settings.CACHE_MIDDLEWARE_KEY_PREFIX 
        self.cache_alias = settings.CACEH_MIDDLEWARE_ALIAS 
        self.cache = caches[self.cache_alias]
        self.get_response = get_response 
    def process_request(self,request):
        if request.method not in ("GET","HEAD"):#POST PATCH DELETE
            request._cache_update_cache = True 
            return None 
        cache_key = get_cache_key(request,self.key_prefix,"GET",cache=self.cache)
        if cache_key is None:
            request._cache_update_cache = True 
            return None 
        response = self.cache.get(cache_key)
        if response is None and request.method == "HEAD":
            cache_key = get_cache_key(
                request,self.key_prefix,"HEAD",cache=self.cache
            )
        response = self.cache.get(cache_key)
        if response is None:
            request._cache_update_cache = True 
            return None 
        request._cache_update_cache = True 
        return response 
