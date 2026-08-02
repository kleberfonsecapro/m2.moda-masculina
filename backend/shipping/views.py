import json
from decimal import Decimal, InvalidOperation

from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .services import lookup_cep, quote


@require_POST
def cep_lookup(request):
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Dados inválidos'}, status=400)

    cep = str(data.get('cep', '')).replace('-', '').strip()
    if len(cep) != 8 or not cep.isdigit():
        return JsonResponse({'error': 'CEP inválido. Digite 8 dígitos.'}, status=400)

    address = lookup_cep(cep)
    if not address:
        return JsonResponse({'error': 'CEP não encontrado.'}, status=404)

    return JsonResponse({
        'success': True,
        'logradouro': address.get('logradouro', ''),
        'bairro': address.get('bairro', ''),
        'localidade': address.get('localidade', ''),
        'uf': address.get('uf', ''),
    })


@require_POST
def shipping_quote(request):
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Dados inválidos'}, status=400)

    cep = str(data.get('cep', '')).replace('-', '').strip()
    if len(cep) != 8 or not cep.isdigit():
        return JsonResponse({'error': 'CEP inválido. Digite 8 dígitos.'}, status=400)

    address = lookup_cep(cep)
    if not address:
        return JsonResponse({'error': 'CEP não encontrado.'}, status=404)

    subtotal = data.get('subtotal')
    if subtotal is not None:
        try:
            subtotal = Decimal(str(subtotal))
        except (InvalidOperation, ValueError):
            subtotal = None

    options = quote(cep, subtotal=subtotal)
    if not options:
        return JsonResponse({
            'success': True,
            'address': f"{address.get('localidade', '')} - {address.get('uf', '')}",
            'options': [],
        })

    return JsonResponse({
        'success': True,
        'address': f"{address.get('localidade', '')} - {address.get('uf', '')}",
        'options': [
            {'name': option['name'], 'value': str(option['value'])}
            for option in options
        ],
    })
