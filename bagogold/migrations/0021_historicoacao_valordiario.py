# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bagogold', '0020_operacaoacao_destinacao'),
    ]

    operations = [
        migrations.CreateModel(
            name='HistoricoAcao',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('data', models.DateField(verbose_name='Data')),
                ('preco_unitario', models.DecimalField(verbose_name='Pre\xe7o unit\xe1rio', max_digits=11, decimal_places=2)),
                ('acao', models.ForeignKey(to='bagogold.Acao', unique_for_date=b'data')),
            ],
        ),
        migrations.CreateModel(
            name='ValorDiario',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('data_hora', models.DateTimeField(verbose_name='Hor\xe1rio')),
                ('preco_unitario', models.DecimalField(verbose_name='Pre\xe7o unit\xe1rio', max_digits=11, decimal_places=2)),
                ('acao', models.ForeignKey(to='bagogold.Acao')),
            ],
        ),
    ]
