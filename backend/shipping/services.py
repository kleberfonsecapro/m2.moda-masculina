import json
import math
from decimal import Decimal, ROUND_HALF_UP

from urllib.request import urlopen
from urllib.error import URLError, HTTPError

from .models import ShippingConfig, ShippingRegion, ShippingRate

CUBAGE_FACTOR = 6000
VIACEP_URL = 'https://viacep.com.br/ws/{cep}/json/'


def _normalize_cep(cep):
    cep = (cep or '').replace('-', '').replace('.', '').strip()
    return cep if cep.isdigit() and len(cep) == 8 else ''


def lookup_cep(cep):
    cep = _normalize_cep(cep)
    if not cep:
        return None
    try:
        with urlopen(VIACEP_URL.format(cep=cep), timeout=4) as response:
            data = json.loads(response.read().decode('utf-8'))
    except (URLError, HTTPError, OSError, ValueError, TimeoutError):
        return None
    if data.get('erro'):
        return None
    return data


def _postal_weight(config):
    cubic = (
        float(config.comprimento_cm) * float(config.largura_cm) * float(config.altura_cm)
    ) / CUBAGE_FACTOR
    return int(math.ceil(max(float(config.peso_padrao_kg), cubic)))


def _region_factor(config, cep_destino):
    regions = ShippingRegion.objects.filter(
        ativo=True,
        cep_inicio__lte=cep_destino,
        cep_fim__gte=cep_destino,
    )
    region = regions.order_by('-cep_inicio').first()
    return region.fator if region else Decimal('1.00')


def _format(value):
    return value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def quote(cep_destino, subtotal=None):
    config = ShippingConfig.objects.first()
    if not config or not config.ativo:
        return []

    cep = _normalize_cep(cep_destino)
    if not cep:
        return []

    peso = _postal_weight(config)
    fator = _region_factor(config, cep)

    options = []
    rates = ShippingRate.objects.filter(
        ativo=True,
        peso_min_kg__lte=peso,
        peso_max_kg__gte=peso,
    ).order_by('valor_base')

    for rate in rates:
        value = _format(rate.valor_base * fator)
        if subtotal is not None and config.frete_gratis_acima_de and subtotal >= config.frete_gratis_acima_de:
            value = Decimal('0.00')
        options.append({
            'name': rate.nome,
            'value': value,
        })
    return options
