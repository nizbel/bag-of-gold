# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2018-04-28 20:14
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lci_lca', '0006_auto_20180425_1217'),
    ]

    operations = [
        migrations.AlterField(
            model_name='historicoporcentagemletracredito',
            name='porcentagem',
            field=models.DecimalField(decimal_places=2, max_digits=5, verbose_name='Porcentagem de rendimento'),
        ),
    ]
