# Generated by Django 5.0.1 on 2024-01-27 08:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('calc', '0002_delete_area_difference'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='point_ac',
            field=models.DecimalField(blank=True, decimal_places=8, max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name='profile',
            name='point_as',
            field=models.DecimalField(blank=True, decimal_places=8, max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name='profile',
            name='point_cc',
            field=models.DecimalField(blank=True, decimal_places=8, max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name='profile',
            name='point_ct',
            field=models.DecimalField(blank=True, decimal_places=8, max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name='profile',
            name='point_cw',
            field=models.DecimalField(blank=True, decimal_places=8, max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name='profile',
            name='total',
            field=models.DecimalField(blank=True, decimal_places=8, max_digits=10, null=True),
        ),
    ]