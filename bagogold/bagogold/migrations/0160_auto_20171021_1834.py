# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-10-21 20:34
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bagogold', '0159_auto_20170929_1104'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='titulo',
            unique_together=set([('tipo', 'data_vencimento')]),
        ),
    ]
