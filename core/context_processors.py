from django.conf import settings


def turnstile(request):
    """Expose la clé publique Turnstile aux templates (chaîne vide si non configurée)."""
    return {"TURNSTILE_SITE_KEY": settings.TURNSTILE_SITE_KEY}


def analytics(request):
    """Expose la configuration Plausible aux templates.

    Le template n'injecte le script que pour les visiteurs anonymes, ce qui
    exclut les utilisateur·ice·s connecté·e·s des statistiques d'audience.
    Les valeurs sont des chaînes vides si la mesure n'est pas configurée
    (dev, tests, CI).
    """
    return {
        "PLAUSIBLE_DOMAIN": settings.PLAUSIBLE_DOMAIN,
        "PLAUSIBLE_SCRIPT_URL": settings.PLAUSIBLE_SCRIPT_URL,
    }


def site_url(request):
    """Expose l'URL publique du site (WAGTAILADMIN_BASE_URL) aux templates.

    Utilisée pour canonical/og:url : on construit l'URL publique réelle
    (https://latribudoya.fr{path}) indépendamment de l'hôte de la requête et
    de l'enregistrement Wagtail Site (dont le hostname peut pointer vers un
    hôte interne non résolu publiquement).
    """
    base_url = getattr(settings, "WAGTAILADMIN_BASE_URL", "").rstrip("/")
    return {"SITE_BASE_URL": base_url}
