# Generated by Django 2.2.9 on 2022-01-15 15:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0003_remove_group_slug'),
    ]

    operations = [
        migrations.AddField(
            model_name='group',
            name='slug',
            field=models.SlugField(default='none', max_length=200),
        ),
    ]