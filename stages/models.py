from django.db import models
from modelcluster.fields import ParentalKey
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel
from wagtail.fields import RichTextField
from wagtail.models import Orderable, Page
from wagtail.search import index

CREDIT_FEATURES = ["bold", "italic", "link"]


class StageIndexPage(Page):
    """Listing page for all the workshops (/stages/)."""

    intro = RichTextField(blank=True)

    max_count = 1
    parent_page_types = ["home.HomePage"]
    subpage_types = ["stages.StagePage"]

    content_panels = Page.content_panels + [FieldPanel("intro")]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context["stages"] = (
            StagePage.objects.child_of(self).live().order_by("ordre")
        )
        return context

    class Meta:
        verbose_name = "Page index des stages"


class StagePage(Page):
    """A single workshop / stage."""

    type = models.CharField(max_length=255, blank=True, default="Stage de théâtre")
    subtitle = models.CharField(max_length=255, blank=True)
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
    description_courte = models.CharField(
        "Description courte", max_length=255, blank=True
    )
    intention = RichTextField(blank=True)
    theme = RichTextField("Thème", blank=True)
    note = RichTextField(blank=True)
    youtube_link = models.URLField(
        "Lien YouTube (embed)", blank=True,
        help_text="URL d'intégration, ex: https://www.youtube.com/embed/XXXX",
    )

    parent_page_types = ["stages.StageIndexPage"]
    subpage_types = []

    content_panels = Page.content_panels + [
        MultiFieldPanel(
            [
                FieldPanel("type"),
                FieldPanel("subtitle"),
                FieldPanel("ordre"),
            ],
            heading="Informations",
        ),
        FieldPanel("background_image"),
        FieldPanel("credit"),
        FieldPanel("description_courte"),
        FieldPanel("intention"),
        FieldPanel("theme"),
        InlinePanel("objectifs", label="Objectifs"),
        InlinePanel("axes_travail", label="Axes de travail"),
        FieldPanel("note"),
        FieldPanel("youtube_link"),
        InlinePanel("prochaines_dates", label="Prochaines dates"),
    ]

    search_fields = Page.search_fields + [
        index.SearchField("intention"),
        index.SearchField("theme"),
    ]

    @property
    def has_detail_page(self):
        return True

    class Meta:
        verbose_name = "Stage / Atelier"


class StageObjectif(Orderable):
    page = ParentalKey(
        StagePage, on_delete=models.CASCADE, related_name="objectifs"
    )
    texte = models.CharField(max_length=500)

    panels = [FieldPanel("texte")]


class StageAxeTravail(Orderable):
    page = ParentalKey(
        StagePage, on_delete=models.CASCADE, related_name="axes_travail"
    )
    texte = models.CharField(max_length=500)

    panels = [FieldPanel("texte")]


class StageDate(Orderable):
    page = ParentalKey(
        StagePage, on_delete=models.CASCADE, related_name="prochaines_dates"
    )
    date = models.CharField(max_length=255)
    horaires = models.CharField(max_length=255, blank=True)
    lieu = models.CharField(max_length=255, blank=True)
    billetterie = models.URLField("Lien billetterie", blank=True)

    panels = [
        FieldPanel("date"),
        FieldPanel("horaires"),
        FieldPanel("lieu"),
        FieldPanel("billetterie"),
    ]
