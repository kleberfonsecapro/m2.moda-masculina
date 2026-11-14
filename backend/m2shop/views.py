"""Views operacionais: probes consumidos pelos healthchecks do Docker Compose."""
import logging

from django.db import connection
from django.http import JsonResponse

logger = logging.getLogger(__name__)


def healthz(request):
    """Probe de prontidão da aplicação.

    Responde 200 somente quando o processo atende e o banco aceita conexão.
    O corpo não carrega detalhes do erro: healthcheck é público o bastante para
    não virar fonte de reconhecimento de infraestrutura (OWASP A09).
    """
    try:
        connection.ensure_connection()
    except Exception:
        logger.exception('healthz: banco de dados indisponivel')
        return JsonResponse({'status': 'error'}, status=503)

    return JsonResponse({'status': 'ok'})
