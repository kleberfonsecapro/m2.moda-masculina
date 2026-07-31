from django.db import migrations


def seed_default_messages(apps, schema_editor):
    TickerMessage = apps.get_model('catalog', 'TickerMessage')
    if TickerMessage.objects.exists():
        return

    default_phrases = [
        '🔥 Moda masculina com estilo e atitude',
        '🚚 Frete grátis acima de R$ 199',
        '💳 Parcele em até 3x sem juros',
    ]
    for order, phrase in enumerate(default_phrases):
        TickerMessage.objects.create(text=phrase, order=order, active=True)


def remove_seeded_messages(apps, schema_editor):
    TickerMessage = apps.get_model('catalog', 'TickerMessage')
    TickerMessage.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0013_tickermessage'),
    ]

    operations = [
        migrations.RunPython(seed_default_messages, remove_seeded_messages),
    ]
