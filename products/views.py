import logging 
import json
import requests
from django.core.cache import cache
from django.conf import settings 
from django.core.cache.backends.base import DEFAULT_TIMEOUT
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie
from django.utils.translation import ugettext_lazy as _
from rest_framework.decorators import permission_classes
from rest_framework.generics import (
    ListAPIView,RetrieveAPIView,CreateAPIView,DestroyAPIView,
)
from rest_framework import permissions,status
from rest_framework.exceptions import PermissionDenied,NotAcceptable,ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework import viewsets
from django_elasticsearch_dsl_drf.constants import LOOKUP_FILTER_GEO_DISTANCE 
from django_elasticsearch_dsl_drf.filter_backends import (
    FilteringFilterBackend,
    OrderingFilterBackend,
    SearchFilterBackend,
    DefaultOrderingFilterBackend,
)
from django_elasticsearch_dsl_drf.viewsets import DocumentViewSet,BaseDocumentViewSet 
from .models import Category,Product,ProductViews,User
from .serializers import (
    CategoryListSerializer,
    ProductDetailSerializer,
    ProductIndexSerializer,
    ProductViewsSerializer,
    ProductMiniSerializer,
    SerpyProductSerializer,
    CreateProductSerializer,
    ProductDocumentSerializer,
)
from .documents import ProductDocument
from .permissions import IsOwnerAuth,ModelViewSetPermission
from notifications.utils import push_notifications 
from notifications.twilio import send_message 
from core.decorators import time_calculator
from googletrans import Translator 

translator = Translator()
logger = logging.getLogger(__name__)

# Create your views here.
class SerpyListProductAPIView(ListAPIView):
    serializer_class = SerpyProductSerializer
    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    )
    search_fields = ("title",)
    ordering_fields = ("created",)
    filter_fields = ("views",)
    queryset = Product.objects.all()

class ListProductView(viewsets.ModelViewSet):
    permission_classes = (ModelViewSetPermission,)
    serializer_class = CreateProductSerializer
    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    )
    search_fields = ("title",)
    ordering_fields = ("created",)
    filter_fields = ("views",)
    queryset = Product.objects.all()

    def update(self,request,*args,**kwargs):
        from django.contrib.auth.models import User 
        if User.objects.get(username="Sardor")!=self.get_object().seller:
            raise NotAcceptable(_("You don't own product"))
        return super(ListProductView,self).update(request,*args,**kwargs)
        