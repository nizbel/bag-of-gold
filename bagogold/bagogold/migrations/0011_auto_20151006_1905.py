# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bagogold', '0010_auto_20150926_0300'),
    ]

    operations = [
        migrations.AlterField(
            model_name='proventofii',
            name='valor_unitario',
            field=models.DecimalField(verbose_name='Valor unit\xe1rio', max_digits=13, decimal_places=9),
        ),
    ]
