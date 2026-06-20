from django.db import models
from modelcluster.fields import ParentalKey
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel
from wagtail.fields import RichTextField
from wagtail.models import Orderable, Page
from wagtail.search import index

CREDIT_FEATURES = ["bold", "italic", "link"]


class ProjetIndexPage(Page):
    """Listing page for all the theatre projects (/projets/)."""

    intro = RichTextField(blank=True)

    max_count = 1
    parent_page_types = ["home.HomePage"]
    subpage_types = ["projets.ProjetPage"]

    content_panels = Page.content_panels + [FieldPanel("intro")]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context["projets"] = (
            ProjetPage.objects.child_of(self).live().order_by("ordre")
        )
        return context

    class Meta:
        verbose_name = "Page index des projets"


class ProjetPage(Page):
    """A single theatre project / spectacle."""

    subtitle = models.CharField(
        max_length=255, blank=True, default="Pièce de théâtre"
    )
    annee = models.CharField(
        "Année de création", max_length=50, blank=True
    )
    ordre = models.PositiveIntegerField("Ordre d'affichage", default=0)
    background_image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name="Image de fond",
    )
    credit = RichTextField("Crédits", blank=True, features=CREDIT_FEATURES)
    description = RichTextField(blank=True)
    youtube_link = models.URLField(
        "Lien YouTube (embed)", blank=True,
        help_text="URL d'intégration, ex: https://www.youtube.com/embed/XXXX",
    )
    press_folder = models.ForeignKey(
        "wagtaildocs.Document",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name="Dossier de presse",
    )
    is_in_progress = models.BooleanField(
        "En cours de création",
        default=False,
        help_text="Si coché, le projet s'affiche sans page de détail "
        "(badge « En cours de création »).",
    )

    parent_page_types = ["projets.ProjetIndexPage"]
    subpage_types = []

    content_panels = Page.content_panels + [
        MultiFieldPanel(
            [
                FieldPanel("subtitle"),
                FieldPanel("annee"),
                FieldPanel("ordre"),
                FieldPanel("is_in_progress"),
            ],
            heading="Informations",
        ),
        FieldPanel("background_image"),
        FieldPanel("credit"),
        FieldPanel("description"),
        FieldPanel("youtube_link"),
        FieldPanel("press_folder"),
        InlinePanel("gallery_images", label="Galerie d'images"),
    ]

    search_fields = Page.search_fields + [
        index.SearchField("description"),
        index.SearchField("credit"),
    ]

    @property
    def has_detail_page(self):
        return not self.is_in_progress

    class Meta:
        verbose_name = "Projet / Spectacle"


class ProjetGalleryImage(Orderable):
    page = ParentalKey(
        ProjetPage, on_delete=models.CASCADE, related_name="gallery_images"
    )
    image = models.ForeignKey(
        "wagtailimages.Image",
        on_delete=models.CASCADE,
        related_name="+",
    )

    panels = [FieldPanel("image")]
