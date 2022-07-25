# Generated by Django 3.2.2 on 2022-05-08 19:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0003_jobs_job_title'),
    ]

    operations = [
        migrations.AddField(
            model_name='jobs',
            name='job_category',
            field=models.CharField(default='IT', max_length=20),
        ),
        migrations.AddField(
            model_name='jobs',
            name='job_type',
            field=models.CharField(default='fulltime', max_length=20),
        ),
        migrations.AlterField(
            model_name='jobs',
            name='job_title',
            field=models.CharField(default='junior', max_length=20),
        ),
    ]