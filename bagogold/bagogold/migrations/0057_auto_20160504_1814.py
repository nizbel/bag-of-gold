# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-05-04 21:14
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bagogold', '0056_empresa_nome_pregao'),
    ]

    operations = [
        migrations.AlterField(
            model_name='provento',
            name='data_pagamento',
            field=models.DateField(blank=True, null=True, verbose_name='Data do pagamento'),
        ),
    ]
