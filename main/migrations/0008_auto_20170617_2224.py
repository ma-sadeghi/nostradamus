# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-06-17 22:24
from __future__ import unicode_literals

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0007_auto_20170617_2223'),
    ]

    operations = [
        migrations.AlterField(
            model_name='game',
            name='scheduled_datetime',
            field=models.DateTimeField(default=datetime.datetime(2017, 6, 17, 22, 24, 28, 961225, tzinfo=utc)),
        ),
    ]
