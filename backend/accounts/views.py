from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from .forms import UserRegistrationForm
from .models import EmailVerificationToken


@ratelimit(key='ip', rate='5/m', method='POST', block=True)
def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            messages.success(
                request,
                'Cadastro realizado! Enviamos um e-mail de confirmação para ativar sua conta.',
            )
            return redirect('catalog:home')
    else:
        form = UserRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})


def verify_email(request, token):
    token_obj = get_object_or_404(EmailVerificationToken, token=token)
    user = token_obj.user
    if not user.is_active:
        user.is_active = True
        user.save()
        token_obj.delete()
        messages.success(request, 'E-mail confirmado! Faça login para continuar.')
    else:
        messages.info(request, 'Esta conta já está ativa.')
    return redirect('accounts:login')


@method_decorator(ratelimit(key='ip', rate='10/m', method='POST', block=True), name='dispatch')
class RateLimitedLoginView(LoginView):
    template_name = 'accounts/login.html'


@login_required
def profile(request):
    return render(request, 'accounts/profile.html')
