# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-12-18 17:56
from __future__ import unicode_literals

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bagogold', '0105_auto_20161218_1536'),
    ]

    operations = [
        migrations.AlterField(
            model_name='investidorrecusadocumento',
            name='motivo',
            field=models.CharField(max_length=500, validators=[django.core.validators.MinLengthValidator(10)], verbose_name='Motivo da recusa'),
        ),
    ]
