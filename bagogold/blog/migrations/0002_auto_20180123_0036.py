# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2018-01-23 02:36
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0001_initial'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='categoriapostagem',
            unique_together=set([('postagem', 'categoria')]),
        ),
    ]
