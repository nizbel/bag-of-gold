# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2018-02-06 21:10
from __future__ import unicode_literals

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bagogold', '0168_auto_20171126_2003'),
    ]

    operations = [
        migrations.AlterField(
            model_name='divisaooperacaofii',
            name='quantidade',
            field=models.IntegerField(validators=[django.core.validators.MinValueValidator(1)], verbose_name=b'Quantidade'),
        ),
    ]