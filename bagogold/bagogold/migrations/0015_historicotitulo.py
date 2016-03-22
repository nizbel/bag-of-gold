# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bagogold', '0014_titulo_titulooperacao'),
    ]

    operations = [
        migrations.CreateModel(
            name='HistoricoTitulo',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('data', models.DateField(verbose_name='Data')),
                ('taxa_compra', models.DecimalField(verbose_name='Taxa de compra', max_digits=5, decimal_places=2)),
                ('taxa_venda', models.DecimalField(verbose_name='Taxa de venda', max_digits=5, decimal_places=2)),
                ('preco_compra', models.DecimalField(verbose_name='Pre\xe7o de compra', max_digits=11, decimal_places=2)),
                ('preco_venda', models.DecimalField(verbose_name='Pre\xe7o de venda', max_digits=11, decimal_places=2)),
                ('titulo', models.ForeignKey(to='bagogold.Titulo')),
            ],
        ),
    ]
