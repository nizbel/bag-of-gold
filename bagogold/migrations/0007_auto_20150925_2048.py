# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bagogold', '0006_operacaoacao_data'),
    ]

    operations = [
        migrations.CreateModel(
            name='OperacaoCompraVenda',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('day_trade', models.NullBooleanField(default=False, verbose_name='\xc9 day trade?')),
                ('compra', models.ForeignKey(related_name='compra', to='bagogold.OperacaoAcao')),
                ('venda', models.ForeignKey(related_name='venda', to='bagogold.OperacaoAcao')),
            ],
        ),
        migrations.RemoveField(
            model_name='operacao',
            name='compra',
        ),
        migrations.RemoveField(
            model_name='operacao',
            name='venda',
        ),
        migrations.DeleteModel(
            name='Operacao',
        ),
    ]
