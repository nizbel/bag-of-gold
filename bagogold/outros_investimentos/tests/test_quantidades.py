# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from django.test import TestCase

class QuantidadesOutrosInvestimentosTestCase(TestCase):
    
    def setUp(self):
        user = User.objects.create(username='tester')
        
        
