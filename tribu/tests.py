"""robots.txt et sitemap.xml — fichiers SEO servis à la racine du site.

Le sitemap Wagtail liste les pages live et publiques du site par défaut ;
le protocole des URLs suit la requête (https en production grâce à nginx
qui propage X-Forwarded-Proto, cf. SECURE_PROXY_SSL_HEADER dans les
settings de production).
"""

import xml.etree.ElementTree as ET

from wagtail.test.utils import WagtailPageTestCase
from wagtail.models import Page, Site

from compagnie.models import CompagniePage, MembrePage
from contact.models import FormPage
from home.models import HomePage
from projets.models import ProjetIndexPage, ProjetPage
from pros.models import ProPage
from reseaux.models import ReseauxPage
from stages.models import StageIndexPage, StagePage

HOST = "latribudoya.fr"
BASE_URL = f"https://{HOST}"

# Pages publiques attendues dans le sitemap (chemins de production).
EXPECTED_PATHS = [
    "/",
    "/compagnie/",
    "/compagnie/aude/",
    "/compagnie/stephanie/",
    "/compagnie/louis/",
    "/compagnie/nicolas/",
    "/contact/",
    "/programmer-un-spectacle/",
    "/projets/",
    "/projets/olympe/",
    "/projets/trafiquee/",
    "/projets/jeanne-chauvin/",
    "/reseaux/",
    "/stages/",
    "/stages/choeur-de-femmes/",
]


class SeoRootFilesTests(WagtailPageTestCase):
    """robots.txt et sitemap.xml à la racine du site."""

    def setUp(self):
        root_page = Page.get_first_root_node()
        # Le cache global wagtail_site_root_paths (1 h) peut contenir les Sites
        # créés par d'autres classes de test (ex. « testsite ») : on le purge
        # pour que get_full_url / sitemap utilisent bien notre Site.
        Site.clear_site_root_paths_cache()

        self.home = HomePage(title="Accueil")
        root_page.add_child(instance=self.home)

        # On met à jour le Site par défaut (créé par home/0002 en localhost)
        # au lieu d'en créer un second : la prod fera pareil via la migration
        # home/0008_fix_site_hostname (latribudoya.fr:443 → root_url https).
        Site.objects.update_or_create(
            is_default_site=True,
            defaults={"hostname": HOST, "port": 443, "root_page": self.home},
        )
        Site.clear_site_root_paths_cache()

        self.compagnie = CompagniePage(title="La compagnie", slug="compagnie")
        self.home.add_child(instance=self.compagnie)
        for nom in ("aude", "stephanie", "louis", "nicolas"):
            self.compagnie.add_child(instance=MembrePage(title=nom, slug=nom))

        self.home.add_child(instance=FormPage(title="Contact", slug="contact"))
        self.home.add_child(
            instance=ProPage(title="Programmer un spectacle", slug="programmer-un-spectacle")
        )

        self.projets = ProjetIndexPage(title="Projets", slug="projets")
        self.home.add_child(instance=self.projets)
        for slug in ("olympe", "trafiquee", "jeanne-chauvin"):
            self.projets.add_child(instance=ProjetPage(title=slug, slug=slug))

        self.home.add_child(instance=ReseauxPage(title="Réseaux", slug="reseaux"))

        self.stages = StageIndexPage(title="Stages", slug="stages")
        self.home.add_child(instance=self.stages)
        self.stages.add_child(
            instance=StagePage(title="Chœur de femmes", slug="choeur-de-femmes")
        )

    def test_robots_txt_served(self):
        response = self.client.get("/robots.txt")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/plain")
        self.assertContains(response, "User-agent: *")
        self.assertContains(response, "Allow: /")
        self.assertContains(response, "Sitemap: https://latribudoya.fr/sitemap.xml")

    def test_sitemap_xml_served(self):
        response = self.client.get(
            "/sitemap.xml", secure=True, HTTP_HOST=HOST
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/xml")

        root = ET.fromstring(response.content)
        namespaces = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        urls = [loc.text for loc in root.findall("sm:url/sm:loc", namespaces)]

        self.assertEqual(len(urls), len(EXPECTED_PATHS))
        self.assertEqual(urls, [f"{BASE_URL}{path}" for path in EXPECTED_PATHS])

    def test_sitemap_excludes_draft_pages(self):
        # Une page non publiée ne doit pas apparaître dans le sitemap.
        self.projets.add_child(
            instance=ProjetPage(title="Spectacle brouillon", slug="brouillon", live=False)
        )

        response = self.client.get("/sitemap.xml", secure=True, HTTP_HOST=HOST)
        self.assertNotContains(response, "brouillon")
