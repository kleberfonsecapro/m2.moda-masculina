from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0014_seed_ticker_messages'),
    ]

    operations = [
        migrations.DeleteModel(
            name='CarouselSettings',
        ),
        migrations.DeleteModel(
            name='CarouselSlide',
        ),
    ]
