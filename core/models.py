import uuid
from .managers import SoftDeleteManager
from django.db import models

# Create your models here.

class TimeStampedModel(models.Model):
    created = models.DateTimeField(db_index=True,auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True 

class Extensions(models.Model):
    uuid = models.UUIDField(db_index=True,default=uuid.uuid4,editable=False)
    created = models.DateTimeField(db_index=True,auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    class Meta:
        abstract = True 

class UUIDModel(models.Model):
    uuid = models.UUIDField(db_index=True,default=uuid.uuid4,editable=False)
    class Meta:
        abstract = True
class SoftDeleteModel(models.Model):
    is_deleted = models.BooleanField(default=False)
    objects = SoftDeleteManager()
    class Meta:
        abstract = True 
        