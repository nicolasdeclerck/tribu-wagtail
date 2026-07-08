"""Vérification serveur des jetons Cloudflare Turnstile.

Si `TURNSTILE_SECRET_KEY` n'est pas configurée (dev, tests, CI), la
vérification est considérée comme réussie afin de ne pas bloquer les
environnements sans clés. En production, renseigner les variables
d'environnement `TURNSTILE_SITE_KEY` et `TURNSTILE_SECRET_KEY`.
"""

import json
from urllib import error, parse, request

from django.conf import settings

SITEVERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"


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
        return False

    payload = {"secret": secret, "response": token}
    if remoteip:
        payload["remoteip"] = remoteip

    data = parse.urlencode(payload).encode()
    try:
        with request.urlopen(SITEVERIFY_URL, data=data, timeout=timeout) as resp:
            result = json.loads(resp.read().decode())
    except (error.URLError, ValueError, TimeoutError):
        return False

    return bool(result.get("success"))
