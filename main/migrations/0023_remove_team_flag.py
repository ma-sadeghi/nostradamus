# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2018-06-13 21:10
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0022_bet_contest'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='team',
            name='flag',
        ),
    ]