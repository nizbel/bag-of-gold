# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2019-03-07 03:10
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('acoes', '0005_auto_20190307_0009'),
    ]

    operations = [
        migrations.AlterField(
            model_name='proventoacao',
            name='tipo_provento',
            field=models.SmallIntegerField(verbose_name='Tipo de provento'),
        ),
    ]
