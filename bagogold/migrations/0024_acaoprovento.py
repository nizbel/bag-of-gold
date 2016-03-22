# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bagogold', '0023_usoproventosoperacaoacao'),
    ]

    operations = [
        migrations.CreateModel(
            name='AcaoProvento',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('data_pagamento_frac', models.DateField(verbose_name='Data do pagamento de fra\xe7\xf5es')),
                ('valor_calculo_frac', models.DecimalField(verbose_name='Valor para c\xe1lculo das fra\xe7\xf5es', max_digits=11, decimal_places=2)),
                ('acao_recebida', models.ForeignKey(to='bagogold.Acao')),
                ('provento', models.ForeignKey(to='bagogold.Provento')),
            ],
        ),
    ]
