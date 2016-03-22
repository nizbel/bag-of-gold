# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bagogold', '0025_auto_20151027_1944'),
    ]

    operations = [
        migrations.AlterField(
            model_name='acaoprovento',
            name='data_pagamento_frac',
            field=models.DateField(null=True, verbose_name='Data do pagamento de fra\xe7\xf5es', blank=True),
        ),
    ]
