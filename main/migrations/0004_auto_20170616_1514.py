# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-06-16 15:14
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0003_auto_20170616_1445'),
    ]

    operations = [
        migrations.RenameField(
            model_name='bet',
            old_name='game',
            new_name='game_id',
        ),
        migrations.RenameField(
            model_name='bet',
            old_name='user',
            new_name='user_id',
        ),
    ]
