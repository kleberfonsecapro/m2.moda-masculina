import os

from django import template
from django.conf import settings
from django.templatetags.static import static

register = template.Library()


@register.simple_tag
def static_versioned(path):
    for source_dir in settings.STATICFILES_DIRS:
        full_path = os.path.join(str(source_dir), path)
        try:
            version = int(os.path.getmtime(full_path))
        except OSError:
            continue
        return '%s?v=%d' % (static(path), version)
    return static(path)
