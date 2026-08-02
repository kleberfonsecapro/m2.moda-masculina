from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods


def manager_login(request):
    if request.user.is_authenticated and (request.user.is_superuser or request.user.groups.filter(name='Gerentes').exists()):
        return redirect('management:dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            if user.is_superuser or user.groups.filter(name='Gerentes').exists():
                login(request, user)
                return redirect('management:dashboard')
            else:
                messages.error(request, 'Acesso restrito a gerentes.')
        else:
            messages.error(request, 'Usuário ou senha inválidos.')

    return render(request, 'management/login.html')


@login_required
def manager_logout(request):
    from django.contrib.auth import logout
    logout(request)
    return redirect('management:login')