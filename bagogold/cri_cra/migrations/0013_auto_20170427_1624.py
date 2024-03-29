# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2017-04-27 19:24
from __future__ import unicode_literals

from decimal import Decimal
import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cri_cra', '0012_auto_20170317_0219'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cri_cra',
            name='valor_emissao',
            field=models.DecimalField(decimal_places=8, max_digits=15, validators=[django.core.validators.MinValueValidator(Decimal('1E-8'))], verbose_name='Valor nominal na emiss\xe3o'),
        ),
    ]
