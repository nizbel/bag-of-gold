# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-03-22 00:19
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bagogold', '0044_auto_20160321_2006'),
    ]

    operations = [
        migrations.AlterField(
            model_name='historicocarencialetracredito',
            name='carencia',
            field=models.IntegerField(verbose_name='Per\xedodo de car\xeancia'),
        ),
    ]
