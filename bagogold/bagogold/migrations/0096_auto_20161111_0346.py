# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-11-11 05:46
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bagogold', '0095_auto_20161111_0345'),
    ]

    operations = [
        migrations.AlterField(
            model_name='proventoacaodocumento',
            name='versao',
            field=models.PositiveSmallIntegerField(verbose_name='Vers\xe3o'),
        ),
    ]
