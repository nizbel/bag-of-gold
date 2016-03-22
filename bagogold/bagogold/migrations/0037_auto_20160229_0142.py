# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bagogold', '0036_auto_20160228_2134'),
    ]

    operations = [
        migrations.RenameField(
            model_name='valordiariofii',
            old_name='acao',
            new_name='fii',
        ),
    ]
