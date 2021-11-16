import logging 
import json
from django.utils import translation
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
    ProductSerializer,
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


class ProductDocumentView(DocumentViewSet):
    document = ProductDocument
    serializer_class = ProductDocumentSerializer
    lookup_field = "id"
    filter_backends = [
        FilteringFilterBackend,
        OrderingFilterBackend,
        DefaultOrderingFilterBackend,
        SearchFilterBackend,
    ]        
    search_fields = ("title")
    filter_fields = {"title":"title.raw"}
    ordering_fields = {"created":"created"}
    queryset = Product.objects.all()

class CategoryListAPIView(ListAPIView):
    serializer_class = CategoryListSerializer 
    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    )   
    search_fields = ("name",)
    ordering_fields = ("created",)
    filter_fields = ("created",)

    @time_calculator
    def time(self):
        return 0
    def get_queryset(self):
        queryset = Category.objects.all()
        self.time()
        return queryset 

class CategoryAPIView(RetrieveAPIView):
    serializer_class = CategoryListSerializer
    queryset = Category.objects.all()
    def retrive(self,request,*args,**kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = {}
        for k,v in serializer.data.items():
            data[k]=translator.translate(str(v),dest="ar").text 
        return Response(data)
class ListProductAPIView(ListAPIView):
    serializer_class = ProductSerializer
    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    )    
    search_fieds = ("title",)
    ordering_fields = ("created",)
    filter_fields = ("views",)
    queryset = Product.objects.all()
    @time_calculator
    def time(self):
        return 0
    @method_decorator(cache_page(60*60*2))
    @method_decorator(vary_on_cookie)
    def list(self,request,*args,**kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page,many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset,many=True)
        self.time()
        return Response(serializer.data)
class ListUserProductAPIView(ListAPIView):
    serializer_class = ProductSerializer
    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    )  
    search_fields = (
        "title",
        "user__username",
    )
    ordering_fields = ("created",)
    filter_fields = ("views",)
    def get_queryset(self):
        user = self.request.user 
        queryset = Product.objects.filter(user=user)
        return queryset
    
class CreateProductAPIView(CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CreateProductSerializer
    def create(self,request,*args,**kwargs):
        user = request.user 
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(seller=user)
        push_notifications(user,request.data["title"],"you have add a new product")
        logger.info(
            "product ("
            +str(serializer.data.get("title"))
            +") created"
            + "by ( "
            +str(user.username)
            + " )"
        )
        return Response(serializer.data,status=status.HTTP_201_CREATED)

class DestroyProductAPIView(DestroyAPIView):
    permission_classes = [IsOwnerAuth]
    serializer_class = ProductDetailSerializer 
    queryset = Product.objects.all()
    def destroy(self,request,*args,**kwargs):
        instance = self.get_object()
        instance.is_deleted = True 
        instance.save()
        return Response({"detail":"Product deleted"})
class ProductViewAPIView(ListAPIView):
    serializer_class = ProductViewsSerializer
    queryset = ProductViews.objects.all()

class ProductDetailView(APIView):
    def get(self,request,uuid):
        product = Product.objects.get(uuid=uuid)
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        if not ProductViews.objects.filter(product=product,ip=ip).exists():
            ProductViews.objects.create(product=product,ip=ip)
            product.views += 1
            product.save()
        serializer = ProductDetailSerializer(product,context={"request":request})
        return Response(serializer.data,status=status.HTTP_200_OK)
    def put(self,request,pk):
        user = request.user 
        product = get_object_or_404(Product,pk=pk)
        if product.user != user:
            serializer = ProductDetailSerializer(
                product,data=request.data,context={"request":request}
            )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

class ListMicroServiceView(ListAPIView):
    serializer_class = ProductSerializer 
    queryset = Product.objects.all()

class MicroServiceCreateView(CreateAPIView):
    serializer_class = ProductSerializer 
    queryset = Product.objects.all()

class GETRequests(APIView):
    def get(self,request,*args,**kwargs):
        url = "http://127.0.0.1:8000/micro/"
        response = request.get(url)
        json_content = json.loads(response.content)
        """
        "id":1,
        "seller":"admin",
        "category":"books",
        "created":"2021-13-11T8:52:12.525458Z",
        "modified":"2021-13-11T8:53:13.151542Z",
        "title":"Django Rest Framework",
        "price":"20000",
        "image":null,
        "description":"Django Rest Framework",
        "quantity":2,
        "views":1,
        """
        print(response.headers)
        return Response(json_content)
class POSTRequests(APIView):
    def post(self,request,*args,**kwargs):
        url = "http://127.0.0.1:8000/micro/create/"
        content_type = "application/json;charset=utf-8"
        data = {
            "id":60,
            "seller":"Sardor",
            "title":"post from requests",
            "price":"1000.0",
            "description":"post from requests",
            "quantity":9,
            "views":100,
        }
        response = requests.post(url,data=data)
        return Response("Success")
        
        

