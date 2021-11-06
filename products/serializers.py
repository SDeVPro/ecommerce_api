import json
from re import S 
import serpy 
from rest_framework import serializers
from django.contrib.auth.models import User 
from .models import Category,Product,ProductViews
from drf_extra_fields.fields import Base64ImageField 
from drf_haystack.serializers import HayStackSerializer 
from django_elasticsearch_dsl_drf.serializers import DocumentSerializer 
from .documents import ProductDocument 
from ecommerce.serializers import LightSerializer, LightDictSerializer
from .search_indexes import ProductIndex 

class CategoryListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        exclude = "modified"

class ProductSerializer(serializers.ModelSerializer):
    seller = serializers.SlugRelatedField(slug_field="username",queryset=User.objects)
    category = serializers.SerializerMethodField()

    def get_category(self,obj):
        return obj.category.name 
    class Meta:
        model = Product
        exclude = "modified"
    
class SerpyProductSerializer(serpy.Serializer):
    seller = serpy.StrField()
    category = serpy.StrField()
    title = serpy.StrField() 
    price = serpy.FloatField()
    image = serpy.StrField() 
    description = serpy.StrField()
    quantity = serpy.IntField()
    views = serpy.IntField()

class ProductMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product 
        fields = ["title"]
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data = serializers.ModelSerializer.to_representation(self,instance)
        return data 
class CreateProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product 
        exclude = ("modified")

class ProductDetailSerializer(serializers.ModelSerializer):
    seller = serializers.SlugRelatedField(slug_field="username",queryset=User.objects)
    category = serializers.SerializerMethodField()
    image = Base64ImageField()
    def get_category(self,obj):
        return obj.category.name 
    class Meta:
        model = Product 
        exclude = "modified"
class ProductViewsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductViews
        exclude = "modified"
class ProductDocumentSerializer(DocumentSerializer):
    seller = serializers.SlugRelatedField(slug_field="username",queryset=User.objects)
    category = serializers.SerializerMethodField()
    def get_category(self,obj):
        return obj.category.name 
    class Meta:
        document = ProductDocument
        exclude = "modified"
class ProductIndexSerializer(HayStackSerializer):
    class Meta:
        index_classes = [ProductIndex]
        fields = ("text","title","category")


