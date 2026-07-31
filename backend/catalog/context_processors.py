from .models import SiteConfig, TickerMessage

DEFAULT_TICKER_MESSAGES = ['🔥 Moda masculina com estilo e atitude']
DEFAULT_TICKER_DURATION = 16


def site_config(request):
    whatsapp_number = ''
    instagram = ''
    facebook = ''
    youtube = ''
    tiktok = ''
    twitter = ''
    email = ''
    try:
        config = SiteConfig.objects.first()
        if config:
            whatsapp_number = config.whatsapp_number
            instagram = config.instagram
            facebook = config.facebook
            youtube = config.youtube
            tiktok = config.tiktok
            twitter = config.twitter
            email = config.email
    except Exception:
        pass
    return {
        'whatsapp_number': whatsapp_number,
        'instagram': instagram,
        'facebook': facebook,
        'youtube': youtube,
        'tiktok': tiktok,
        'twitter': twitter,
        'email': email,
    }


def ticker(request):
    try:
        messages = list(TickerMessage.objects.filter(active=True))
    except Exception:
        messages = []

    if not messages:
        return {
            'ticker_messages': DEFAULT_TICKER_MESSAGES,
            'ticker_duration': DEFAULT_TICKER_DURATION,
        }

    return {
        'ticker_messages': [m.text for m in messages],
        'ticker_duration': max(DEFAULT_TICKER_DURATION, len(messages) * 8),
    }
