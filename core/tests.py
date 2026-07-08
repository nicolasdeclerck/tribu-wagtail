"""Injection du script Plausible (mesure d'audience) dans base.html.

Règle métier : le script n'est rendu que pour les visiteurs ANONYMES et
uniquement si la mesure est configurée (PLAUSIBLE_DOMAIN + PLAUSIBLE_SCRIPT_URL).
Les utilisateur·ice·s connecté·e·s sont exclu·e·s des statistiques.
"""

from django.contrib.auth import get_user_model
from django.test import override_settings

from wagtail.models import Page, Site
from wagtail.test.utils import WagtailPageTestCase

from home.models import HomePage

SCRIPT_URL = "https://stats.example.org/js/script.js"
DOMAIN = "example.org"


class PlausibleSnippetTests(WagtailPageTestCase):
    def setUp(self):
        root_page = Page.get_first_root_node()
        Site.objects.create(hostname="testsite", root_page=root_page, is_default_site=True)
        self.homepage = HomePage(title="Home")
        root_page.add_child(instance=self.homepage)

    def _get_body(self):
        return self.client.get(self.homepage.url).content.decode()

    @override_settings(PLAUSIBLE_DOMAIN="", PLAUSIBLE_SCRIPT_URL="")
    def test_not_rendered_when_unconfigured(self):
        body = self._get_body()

        self.assertNotIn(SCRIPT_URL, body)
        self.assertNotIn("data-domain", body)

    @override_settings(PLAUSIBLE_DOMAIN=DOMAIN, PLAUSIBLE_SCRIPT_URL=SCRIPT_URL)
    def test_rendered_for_anonymous_when_configured(self):
        body = self._get_body()

        self.assertIn(SCRIPT_URL, body)
        self.assertIn(f'data-domain="{DOMAIN}"', body)

    @override_settings(PLAUSIBLE_DOMAIN=DOMAIN, PLAUSIBLE_SCRIPT_URL=SCRIPT_URL)
    def test_not_rendered_for_authenticated_user(self):
        user = get_user_model().objects.create_user(username="editrice", password="motdepasse")
        self.client.force_login(user)

        body = self._get_body()

        # Utilisateur connecté → exclu de la mesure, aucun script injecté.
        self.assertNotIn(SCRIPT_URL, body)
        self.assertNotIn("data-domain", body)

    @override_settings(PLAUSIBLE_DOMAIN=DOMAIN, PLAUSIBLE_SCRIPT_URL="")
    def test_not_rendered_when_only_domain_set(self):
        # Configuration partielle (URL manquante) → pas de script (garde-fou).
        body = self._get_body()

        self.assertNotIn("data-domain", body)
