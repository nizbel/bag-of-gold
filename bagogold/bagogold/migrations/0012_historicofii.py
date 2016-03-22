# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bagogold', '0011_auto_20151006_1905'),
    ]

    operations = [
        migrations.CreateModel(
            name='HistoricoFII',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('preco_unitario', models.DecimalField(verbose_name='Pre\xe7o unit\xe1rio', max_digits=11, decimal_places=2)),
                ('data', models.DateField(verbose_name='Data de refer\xeancia')),
                ('fii', models.ForeignKey(to='bagogold.FII')),
            ],
        ),
    ]
