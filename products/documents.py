from django_elasticsearch_dsl import Document,Index,fields 
from elasticsearch_dsl import analyzer
from django_elasticsearch_dsl.registries import registry
from .models import Product 

products_index = Index("products")
products_index.settings(number_of_shards=1,number_of_replicas=1)

html_strip = analyzer(
    "html_strip",
    tokenizer = "standard",
    filter = ["standard","lowercase","stop","snowball"],
    char_filter = ["html_strip"],
)

@products_index.doc_type
class ProductDocument(Document):
    class Django(object):
        model = Product 