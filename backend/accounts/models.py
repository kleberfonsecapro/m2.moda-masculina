import uuid
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse


class EmailVerificationToken(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Token for {self.user.email}'


@receiver(post_save, sender=User)
def send_verification_email(sender, instance, created, **kwargs):
    if created and not instance.is_superuser:
        token, _ = EmailVerificationToken.objects.get_or_create(user=instance)
        link = f"{settings.SITE_URL}{reverse('accounts:verify_email', args=[token.token])}"
        send_mail(
            subject='Confirme seu e-mail - M2 Moda Masculina',
            message=(
                f'Olá {instance.first_name},\n\n'
                f'Confirme seu e-mail clicando no link abaixo:\n\n'
                f'{link}\n\n'
                f'Se você não criou uma conta, ignore este e-mail.\n\n'
                f'Atenciosamente,\nEquipe M2 Moda Masculina'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[instance.email],
            fail_silently=False,
        )
