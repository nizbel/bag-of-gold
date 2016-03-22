# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bagogold', '0017_auto_20151010_1920'),
    ]

    operations = [
        migrations.CreateModel(
            name='OperacaoTitulo',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('preco_unitario', models.DecimalField(verbose_name='Pre\xe7o unit\xe1rio', max_digits=11, decimal_places=2)),
                ('quantidade', models.IntegerField(verbose_name='Quantidade')),
                ('data', models.DateField(verbose_name='Data', blank=True)),
                ('taxa_bvmf', models.DecimalField(verbose_name='Taxa BVMF', max_digits=11, decimal_places=2)),
                ('taxa_custodia', models.DecimalField(verbose_name='Taxa do agente de cust\xf3dia', max_digits=11, decimal_places=2)),
                ('tipo_operacao', models.CharField(max_length=1, verbose_name='Tipo de opera\xe7\xe3o')),
                ('consolidada', models.NullBooleanField(verbose_name='Consolidada?')),
                ('titulo', models.ForeignKey(to='bagogold.Titulo')),
            ],
        ),
        migrations.RemoveField(
            model_name='titulooperacao',
            name='titulo',
        ),
        migrations.DeleteModel(
            name='TituloOperacao',
        ),
    ]
