from django.db import models
from wagtail.admin.panels import FieldPanel
from wagtail.fields import StreamField
from wagtail.models import Page
from wagtail.search import index

from home.blocks import CustomSectionBlock, FaqBlock


class ArticleBodyBlock(CustomSectionBlock):
    """Palette de blocs d'une page « contenu libre » : tous les blocs de la
    section personnalisable de l'accueil (heading, paragraph, image, button,
    interactive_list, separator, columns) + la FAQ."""

    faq = FaqBlock()

    class Meta:
        label = "Contenu de l'article"


class ArticlePage(Page):
    """Page « contenu libre » réutilisable : bannière + contenu en StreamField.

    Destinée aux pages hub SEO (ex. « Programmer du théâtre engagé ») et à
    tout contenu éditorial nécessitant blocs texte/image/colonnes/FAQ."""

    banner_image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name="Image de bannière",
        help_text="Image de fond de la bannière (optionnelle).",
    )
    body = StreamField(
        ArticleBodyBlock(),
        blank=True,
        verbose_name="Contenu",
        help_text="Contenu libre de la page : titres, textes riches, images, boutons, colonnes, FAQ.",
    )

    parent_page_types = ["home.HomePage"]
    subpage_types = []

    content_panels = Page.content_panels + [
        FieldPanel("banner_image"),
        FieldPanel("body"),
    ]

    search_fields = Page.search_fields + [
        index.SearchField("body"),
    ]

    class Meta:
        verbose_name = "Page contenu libre"
        verbose_name_plural = "Pages contenu libre"
