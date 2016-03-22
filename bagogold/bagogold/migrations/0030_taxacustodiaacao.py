# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bagogold', '0029_usoproventosoperacaofii'),
    ]

    operations = [
        migrations.CreateModel(
            name='TaxaCustodiaAcao',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('valor_mensal', models.DecimalField(verbose_name='Pre\xe7o unit\xe1rio', max_digits=11, decimal_places=2)),
                ('data_vigencia', models.DateField(verbose_name='Data de in\xedcio vig\xeancia')),
            ],
        ),
    ]
