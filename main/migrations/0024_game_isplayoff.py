# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2018-06-29 16:04
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0023_remove_team_flag"),
    ]

    operations = [
        migrations.AddField(
            model_name="game",
            name="isplayoff",
            field=models.BooleanField(default=False),
        ),
    ]
