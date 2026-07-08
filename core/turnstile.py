"""Vérification serveur des jetons Cloudflare Turnstile.

Si `TURNSTILE_SECRET_KEY` n'est pas configurée (dev, tests, CI), la
vérification est considérée comme réussie afin de ne pas bloquer les
environnements sans clés. En production, renseigner les variables
d'environnement `TURNSTILE_SITE_KEY` et `TURNSTILE_SECRET_KEY`.
"""

import json
import logging
from urllib import error, parse, request

from django.conf import settings

SITEVERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"

logger = logging.getLogger(__name__)


def verify_turnstile(token, remoteip=None, timeout=5):
    """Retourne True si le jeton est valide (ou si la clé secrète n'est pas configurée).

    Court-circuite sans appel réseau quand la clé est absente (vérification
    désactivée) ou quand le jeton est vide (échec immédiat). Toute erreur
    réseau ou réponse illisible est traitée comme un échec.
    """
    secret = settings.TURNSTILE_SECRET_KEY
    if not secret:
        return True
    if not token:
        # Widget non résolu côté client (bot, JS bloqué, ou erreur de widget —
        # ex. domaine non déclaré dans le dashboard Cloudflare).
        logger.warning("Soumission sans jeton Turnstile — rejet sans appel réseau.")
        return False

    payload = {"secret": secret, "response": token}
    if remoteip:
        payload["remoteip"] = remoteip

    data = parse.urlencode(payload).encode()
    try:
        with request.urlopen(SITEVERIFY_URL, data=data, timeout=timeout) as resp:
            result = json.loads(resp.read().decode())
    except (error.URLError, ValueError, TimeoutError) as exc:
        logger.warning("Turnstile siteverify injoignable : %s", exc)
        return False

    if not result.get("success"):
        logger.warning(
            "Échec de vérification Turnstile : error-codes=%s",
            result.get("error-codes"),
        )
    return bool(result.get("success"))
