# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-11-06 22:24
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bagogold', '0090_auto_20161106_1500'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='proventoacaodocumento',
            unique_together=set([('documento', 'versao')]),
        ),
        migrations.AlterUniqueTogether(
            name='proventofiidocumento',
            unique_together=set([('documento', 'versao')]),
        ),
    ]
