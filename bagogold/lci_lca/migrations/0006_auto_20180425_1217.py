# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2018-04-25 12:17
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('lci_lca', '0005_letracredito_tipo_rendimento'),
    ]

    operations = [
        migrations.RenameField(
            model_name='HistoricoPorcentagemLetraCredito',
            old_name='porcentagem_di',
            new_name='porcentagem',
        ),
    ]
