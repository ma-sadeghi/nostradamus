# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-06-16 14:45
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0002_auto_20170615_2218'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='bet',
            name='team1_name',
        ),
        migrations.RemoveField(
            model_name='bet',
            name='team2_name',
        ),
    ]