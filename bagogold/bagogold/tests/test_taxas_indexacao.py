# -*- coding: utf-8 -*-
from django.test import TestCase


class DITestCase(TestCase):

    def test_buscar_datas(self):
        """Testa se a busca funciona"""
        
    def test_buscar_datas_anterior_a_ultima(self):
        """Testa buscar datas que não haviam sido preenchidas e são anteriores a ultima data na base"""
        
    def test_buscar_datas_com_datas_registradas(self):
        """Testa a busca quando já existem algumas datas na base"""