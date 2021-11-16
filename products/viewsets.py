from rest_framework import viewsets
from drf_haystack.viewsets import HaystackViewSet
from .models import Product 
from .serializers import ProductIndexSerializer 

class ProductSearchView(HaystackViewSet):
    index_models = [Product]
    serializer_class = ProductIndexSerializer 
    queryset = Product.objects.all()
    