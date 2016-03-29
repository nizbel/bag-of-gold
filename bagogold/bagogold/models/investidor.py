# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from django.db import models
 
class Investidor (models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    def __unicode__(self):
        return self.user.first_name + ' ' + self.user.last_name
    
    