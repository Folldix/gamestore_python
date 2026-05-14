# Generated manually for admin / storefront parity

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='game',
            name='external_cover_url',
            field=models.URLField(blank=True, default='', max_length=512),
        ),
        migrations.AddField(
            model_name='game',
            name='download_size',
            field=models.PositiveBigIntegerField(blank=True, default=0),
        ),
        migrations.AddField(
            model_name='game',
            name='age_rating',
            field=models.CharField(blank=True, default='', max_length=64),
        ),
        migrations.AddField(
            model_name='game',
            name='video_trailer',
            field=models.URLField(blank=True, default='', max_length=512),
        ),
    ]
