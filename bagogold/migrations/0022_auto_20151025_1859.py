# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bagogold', '0021_historicoacao_valordiario'),
    ]

    operations = [
        migrations.CreateModel(
            name='ValorDiarioAcao',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('data_hora', models.DateTimeField(verbose_name='Hor\xe1rio')),
                ('preco_unitario', models.DecimalField(verbose_name='Pre\xe7o unit\xe1rio', max_digits=11, decimal_places=2)),
                ('acao', models.ForeignKey(to='bagogold.Acao')),
            ],
        ),
        migrations.CreateModel(
            name='ValorDiarioTitulo',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('data_hora', models.DateTimeField(verbose_name='Hor\xe1rio')),
                ('taxa_compra', models.DecimalField(verbose_name='Taxa de compra', max_digits=5, decimal_places=2)),
                ('taxa_venda', models.DecimalField(verbose_name='Taxa de venda', max_digits=5, decimal_places=2)),
                ('preco_compra', models.DecimalField(verbose_name='Pre\xe7o de compra', max_digits=11, decimal_places=2)),
                ('preco_venda', models.DecimalField(verbose_name='Pre\xe7o de venda', max_digits=11, decimal_places=2)),
                ('titulo', models.ForeignKey(to='bagogold.Titulo')),
            ],
        ),
        migrations.RemoveField(
            model_name='valordiario',
            name='acao',
        ),
        migrations.AlterField(
            model_name='provento',
            name='tipo_provento',
            field=models.CharField(max_length=1, verbose_name='Tipo de provento', unique_for_date=b'data_ex'),
        ),
        migrations.DeleteModel(
            name='ValorDiario',
        ),
    ]
