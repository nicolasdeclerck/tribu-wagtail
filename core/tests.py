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


class CanonicalUrlTests(WagtailPageTestCase):
    """Canonical & og:url doivent pointer vers l'URL publique réelle.

    Bug (issue #12) : le template utilisait ``page.full_url``, construit depuis
    l'enregistrement Wagtail Site — dont le hostname était un hôte interne
    (``latribudoya``) en production → canonical ``http://latribudoya/...``
    (DNS KO). Le fix construit canonical/og:url depuis ``SITE_BASE_URL``
    (WAGTAILADMIN_BASE_URL), indépendamment de l'enregistrement Site et de
    l'hôte de la requête. La page 404 ne doit plus émettre de canonical vide.
    """

    def setUp(self):
        root_page = Page.get_first_root_node()
        self.homepage = HomePage(title="Home")
        root_page.add_child(instance=self.homepage)
        # Hostname interne, comme en production au moment du bug : l'URL
        # publique émise ne doit PAS en dépendre. Site enraciné sur la
        # homepage, comme en production (url_path "/" → /reseaux/, …).
        Site.objects.create(
            hostname="latribudoya", root_page=self.homepage, is_default_site=True
        )

    def test_canonical_uses_public_base_url(self):
        body = self.client.get(self.homepage.url).content.decode()

        self.assertIn(
            '<link rel="canonical" href="https://latribudoya.fr/" />', body
        )
        self.assertNotIn("http://latribudoya", body)

    def test_og_url_uses_public_base_url(self):
        body = self.client.get(self.homepage.url).content.decode()

        self.assertIn(
            '<meta property="og:url" content="https://latribudoya.fr/" />', body
        )

    def test_canonical_includes_page_path(self):
        from reseaux.models import ReseauxPage

        page = ReseauxPage(title="Reseaux", slug="reseaux")
        self.homepage.add_child(instance=page)
        page.save_revision().publish()

        body = self.client.get(page.url).content.decode()

        self.assertIn(
            '<link rel="canonical" href="https://latribudoya.fr/reseaux/" />',
            body,
        )
        self.assertIn(
            '<meta property="og:url" content="https://latribudoya.fr/reseaux/" />',
            body,
        )

    def test_404_has_no_empty_canonical(self):
        response = self.client.get("/cette-page-nexiste-pas/")

        self.assertEqual(response.status_code, 404)
        body = response.content.decode()
        # Plus de canonical vide (href="") : la balise n'est pas émise du tout.
        self.assertNotIn('rel="canonical"', body)
        self.assertNotIn('property="og:url"', body)
        self.assertNotIn('href=""', body)
