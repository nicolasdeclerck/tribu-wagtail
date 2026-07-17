from home.models import HomePage

from wagtail.models import Page, Site
from wagtail.test.utils import WagtailPageTestCase


class HomeSetUpTests(WagtailPageTestCase):
    """
    Tests for basic page structure setup and HomePage creation.
    """

    def test_root_create(self):
        root_page = Page.objects.get(pk=1)
        self.assertIsNotNone(root_page)

    def test_homepage_create(self):
        root_page = Page.objects.get(pk=1)
        homepage = HomePage(title="Home")
        root_page.add_child(instance=homepage)
        self.assertTrue(HomePage.objects.filter(title="Home").exists())


class HomeTests(WagtailPageTestCase):
    """
    Tests for homepage functionality and rendering.
    """

    def setUp(self):
        """
        Create a homepage instance for testing.
        """
        root_page = Page.get_first_root_node()
        Site.objects.create(hostname="testsite", root_page=root_page, is_default_site=True)
        self.homepage = HomePage(title="Home")
        root_page.add_child(instance=self.homepage)

    def test_homepage_is_renderable(self):
        self.assertPageIsRenderable(self.homepage)

    def test_homepage_template_used(self):
        response = self.client.get(self.homepage.url)
        self.assertTemplateUsed(response, "home/home_page.html")

    def test_no_reservations_section_without_representations(self):
        response = self.client.get(self.homepage.url)
        self.assertNotContains(response, "Réservez vos places")

    def test_reservations_section_lists_representations(self):
        from projets.models import (
            ProjetIndexPage,
            ProjetPage,
            ProjetRepresentation,
        )

        index = ProjetIndexPage(title="Projets")
        self.homepage.add_child(instance=index)
        projet = ProjetPage(title="Mon spectacle")
        index.add_child(instance=projet)
        ProjetRepresentation.objects.create(
            page=projet,
            date="12 juillet 2026",
            horaire="20h30",
            lieu="Théâtre municipal",
            billetterie="https://billetterie.example.com",
        )

        response = self.client.get(self.homepage.url)
        self.assertContains(response, "Réservez vos places")
        self.assertContains(response, "Mon spectacle")
        self.assertContains(response, "12 juillet 2026")
        self.assertContains(response, "20h30")
        self.assertContains(response, "Théâtre municipal")
        self.assertContains(response, "https://billetterie.example.com")

    def test_reservations_section_ignores_unpublished_projects(self):
        from projets.models import (
            ProjetIndexPage,
            ProjetPage,
            ProjetRepresentation,
        )

        index = ProjetIndexPage(title="Projets")
        self.homepage.add_child(instance=index)
        projet = ProjetPage(title="Spectacle brouillon", live=False)
        index.add_child(instance=projet)
        ProjetRepresentation.objects.create(page=projet, date="1 août 2026")

        response = self.client.get(self.homepage.url)
        self.assertNotContains(response, "Réservez vos places")
