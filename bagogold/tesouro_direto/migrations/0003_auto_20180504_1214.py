# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2018-05-04 15:14
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tesouro_direto', '0002_auto_20180424_0152'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='valordiariotitulo',
            unique_together=set([('titulo', 'data_hora')]),
        ),
    ]
