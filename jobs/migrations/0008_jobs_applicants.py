# Generated by Django 3.2.2 on 2022-05-27 17:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0007_auto_20220527_1931'),
    ]

    operations = [
        migrations.AddField(
            model_name='jobs',
            name='applicants',
            field=models.ManyToManyField(blank=True, to='jobs.Applicant'),
        ),
    ]
