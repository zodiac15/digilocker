from django.db import models


# Create your models here.
class UserBlock(models.Model):
    index = models.IntegerField()
    user = models.CharField(max_length=50)
