# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2017-03-12 13:59
from __future__ import unicode_literals

from decimal import Decimal
import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cri_cra', '0009_auto_20170312_1041'),
    ]

    operations = [
        migrations.AlterField(
            model_name='operacaocri_cra',
            name='preco_unitario',
            field=models.DecimalField(decimal_places=2, max_digits=11, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))], verbose_name='Pre\xe7o unit\xe1rio'),
        ),
        migrations.AlterField(
            model_name='operacaocri_cra',
            name='quantidade',
            field=models.IntegerField(validators=[django.core.validators.MinValueValidator(1)], verbose_name='Quantidade'),
        ),
    ]
