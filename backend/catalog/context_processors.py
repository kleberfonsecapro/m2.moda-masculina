from .models import SiteConfig


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
