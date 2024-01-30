# Generated by Django 5.0.1 on 2024-01-22 08:57

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Area_difference',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('difference_category', models.TextField()),
                ('multiple', models.DecimalField(decimal_places=8, max_digits=10)),
            ],
        ),
        migrations.CreateModel(
            name='Manual',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('area', models.TextField()),
                ('upload_date', models.DateTimeField(auto_now_add=True)),
                ('manual', models.FileField(upload_to='manuals/')),
                ('uploader', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('area', models.TextField()),
                ('point_cc', models.DecimalField(decimal_places=8, max_digits=10)),
                ('point_cw', models.DecimalField(decimal_places=8, max_digits=10)),
                ('point_ct', models.DecimalField(decimal_places=8, max_digits=10)),
                ('point_ac', models.DecimalField(decimal_places=8, max_digits=10)),
                ('point_as', models.DecimalField(decimal_places=8, max_digits=10)),
                ('total', models.DecimalField(decimal_places=8, max_digits=10)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Common_WorkPerformance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('workperformance', models.TextField()),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='calc.profile')),
            ],
        ),
        migrations.CreateModel(
            name='Common_Training',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('candidate', models.DecimalField(decimal_places=8, max_digits=10)),
                ('qualification', models.DecimalField(decimal_places=8, max_digits=10)),
                ('training', models.DecimalField(decimal_places=8, max_digits=10)),
                ('competition_memo', models.TextField()),
                ('competition_point', models.DecimalField(decimal_places=8, max_digits=10)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='calc.profile')),
            ],
        ),
        migrations.CreateModel(
            name='Common_carrer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('career_month', models.IntegerField()),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='calc.profile')),
            ],
        ),
        migrations.CreateModel(
            name='Area_Common',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('area', models.TextField()),
                ('research_school_career', models.IntegerField()),
                ('overseas_citizen_institution', models.IntegerField()),
                ('training_year', models.IntegerField()),
                ('school_violence', models.IntegerField()),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='calc.profile')),
            ],
        ),
    ]
