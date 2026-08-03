import re

from django.http import HttpResponseRedirect

MOBILE_USER_AGENT = re.compile(
    r'Android|iPhone|iPod|iPad|Windows Phone|IEMobile|BlackBerry|'
    r'Opera Mini|Mobile|Silk|Kindle|webOS|Fennec|Mobi',
    re.IGNORECASE,
)

BOT_USER_AGENT = re.compile(
    r'bot|crawler|spider|slurp|curl|wget|httpie|postman|urllib|python-requests',
    re.IGNORECASE,
)

EXCLUDED_PREFIXES = (
    '/admin/',
    '/gerencial/',
    '/accounts/',
    '/media/',
    '/static/',
)


def desktop_to_mobile(path):
    if path == '/':
        return '/m/'
    if path == '/produtos/':
        return '/m/produtos/'
    if path.startswith('/produtos/'):
        return '/m/categorias/' + path[len('/produtos/'):]
    if path.startswith('/produto/'):
        return '/m/produto/' + path[len('/produto/'):]
    if path == '/carrinho/':
        return '/m/carrinho/'
    if path == '/checkout/' or path.startswith('/checkout/sucesso/'):
        return '/m' + path
    if path == '/vendas/':
        return '/m/vendas/'
    if path == '/vendas/entrar/':
        return '/m/vendas/entrar/'
    return None


def mobile_to_desktop(path):
    if path == '/m/':
        return '/'
    if path == '/m/categorias/':
        return '/produtos/'
    if path.startswith('/m/categorias/'):
        return '/produtos/' + path[len('/m/categorias/'):]
    if path == '/m/produtos/':
        return '/produtos/'
    if path.startswith('/m/produto/'):
        return '/produto/' + path[len('/m/produto/'):]
    if path == '/m/carrinho/':
        return '/carrinho/'
    if path == '/m/checkout/' or path.startswith('/m/checkout/sucesso/'):
        return path[len('/m'):]
    if path == '/m/vendas/':
        return '/vendas/'
    if path == '/m/vendas/entrar/':
        return '/vendas/entrar/'
    return None


class DeviceRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not self._should_process(request):
            return self.get_response(request)

        mode = request.COOKIES.get('view_mode')
        is_mobile = bool(MOBILE_USER_AGENT.search(request.META.get('HTTP_USER_AGENT', '')))

        if mode == 'mobile':
            target = desktop_to_mobile(request.path)
        elif mode == 'desktop':
            target = mobile_to_desktop(request.path)
        elif is_mobile:
            target = desktop_to_mobile(request.path)
        else:
            target = mobile_to_desktop(request.path)

        if target:
            if request.META.get('QUERY_STRING'):
                target += '?' + request.META['QUERY_STRING']
            return HttpResponseRedirect(target)

        return self.get_response(request)

    @staticmethod
    def _should_process(request):
        if request.method != 'GET':
            return False
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return False
        if request.path.startswith(EXCLUDED_PREFIXES):
            return False
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        if not user_agent or BOT_USER_AGENT.search(user_agent):
            return False
        return True
