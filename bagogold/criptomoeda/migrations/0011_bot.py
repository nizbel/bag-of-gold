# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-08-25 16:41
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('criptomoeda', '0010_auto_20170825_1317'),
    ]

    operations = [
        migrations.CreateModel(
            name='Bot',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ultima_msg_lida', models.IntegerField(verbose_name='ID da \xfaltima mensagem lida')),
            ],
        ),
    ]