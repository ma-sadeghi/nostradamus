# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2018-06-12 15:06
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0020_auto_20180612_1050'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='bet',
            name='game',
        ),
        migrations.AddField(
            model_name='bet',
            name='game',
            field=models.ForeignKey(default=2, on_delete=django.db.models.deletion.CASCADE, related_name='bets', to='main.Game'),
            preserve_default=False,
        ),
    ]
