# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-11-12 21:33
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('YSE_App', '0002_host_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transient',
            name='date_modified',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
