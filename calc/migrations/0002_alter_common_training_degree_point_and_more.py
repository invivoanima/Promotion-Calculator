# Generated by Django 5.0.1 on 2024-02-05 09:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('calc', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='common_training',
            name='degree_point',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='common_training',
            name='grade1teacher_result',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='common_training',
            name='research_contest_point',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='common_training',
            name='training_first',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='common_training',
            name='training_second',
            field=models.IntegerField(default=0),
        ),
    ]
