from home.models import HomePage
from wagtail.models import Page, Site
from wagtail.test.utils import WagtailPageTestCase

from articles.models import ArticlePage


class ArticleTests(WagtailPageTestCase):
    """Tests pour le type de page « contenu libre » (ArticlePage)."""

    def setUp(self):
        root_page = Page.get_first_root_node()
        Site.objects.create(hostname="testsite", root_page=root_page, is_default_site=True)
        self.homepage = HomePage(title="Home")
        root_page.add_child(instance=self.homepage)

    def test_article_can_be_created_under_homepage(self):
        article = ArticlePage(title="Programmer du théâtre engagé")
        self.homepage.add_child(instance=article)
        article.refresh_from_db()
        self.assertEqual(article.get_parent().specific, self.homepage)

    def test_homepage_allows_article_subpage(self):
        self.assertIn(ArticlePage, HomePage.allowed_subpage_models())

    def test_article_is_renderable(self):
        article = ArticlePage(
            title="Programmer du théâtre engagé",
            body=[
                ("heading", {"text": "Un titre"}),
                (
                    "paragraph",
                    {"text": "<p>Un paragraphe.</p>", "size": "base"},
                ),
            ],
        )
        self.homepage.add_child(instance=article)
        article.save_revision().publish()
        self.assertPageIsRenderable(article)

    def test_article_template_used(self):
        article = ArticlePage(title="Programmer du théâtre engagé")
        self.homepage.add_child(instance=article)
        article.save_revision().publish()
        response = self.client.get(article.url)
        self.assertTemplateUsed(response, "articles/article_page.html")

    def test_body_content_renders(self):
        article = ArticlePage(
            title="Programmer du théâtre engagé",
            body=[
                ("heading", {"text": "Un titre bien visible"}),
                (
                    "paragraph",
                    {"text": "<p>Un paragraphe bien visible.</p>", "size": "base"},
                ),
            ],
        )
        self.homepage.add_child(instance=article)
        article.save_revision().publish()
        response = self.client.get(article.url)
        self.assertContains(response, "Un titre bien visible")
        self.assertContains(response, "Un paragraphe bien visible")

    def test_faq_block_renders(self):
        article = ArticlePage(
            title="Programmer du théâtre engagé",
            body=[
                (
                    "faq",
                    {
                        "title": "FAQ",
                        "items": [{"question": "Q1", "answer": "<p>R1</p>"}],
                    },
                ),
            ],
        )
        self.homepage.add_child(instance=article)
        article.save_revision().publish()
        response = self.client.get(article.url)
        self.assertContains(response, "Q1")
