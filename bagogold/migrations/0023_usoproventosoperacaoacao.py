# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bagogold', '0022_auto_20151025_1859'),
    ]

    operations = [
        migrations.CreateModel(
            name='UsoProventosOperacaoAcao',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('qtd_utilizada', models.DecimalField(verbose_name='Quantidade utilizada', max_digits=11, decimal_places=2)),
                ('operacao', models.ForeignKey(to='bagogold.OperacaoAcao')),
            ],
        ),
    ]
