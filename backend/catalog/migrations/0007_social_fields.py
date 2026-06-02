from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0006_siteconfig'),
    ]

    operations = [
        migrations.AddField(
            model_name='siteconfig',
            name='email',
            field=models.EmailField(blank=True, max_length=255, verbose_name='E-mail'),
        ),
        migrations.AddField(
            model_name='siteconfig',
            name='facebook',
            field=models.URLField(blank=True, max_length=255, verbose_name='Facebook'),
        ),
        migrations.AddField(
            model_name='siteconfig',
            name='instagram',
            field=models.URLField(blank=True, max_length=255, verbose_name='Instagram'),
        ),
        migrations.AddField(
            model_name='siteconfig',
            name='tiktok',
            field=models.URLField(blank=True, max_length=255, verbose_name='TikTok'),
        ),
        migrations.AddField(
            model_name='siteconfig',
            name='twitter',
            field=models.URLField(blank=True, max_length=255, verbose_name='Twitter / X'),
        ),
        migrations.AddField(
            model_name='siteconfig',
            name='youtube',
            field=models.URLField(blank=True, max_length=255, verbose_name='YouTube'),
        ),
    ]
