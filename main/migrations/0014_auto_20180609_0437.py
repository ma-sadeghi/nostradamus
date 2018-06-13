# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2018-06-09 08:37
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0013_auto_20180609_0431'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='game',
            name='contest',
        ),
        migrations.AddField(
            model_name='game',
            name='tournament',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='main.Tournament'),
            preserve_default=False,
        ),
    ]