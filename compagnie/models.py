from django.db import models
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.fields import RichTextField
from wagtail.models import Page
from wagtail.search import index


class CompagniePage(Page):
    """The "La compagnie" page (/compagnie/) with the team grid."""

    body = RichTextField(
        "Texte de présentation", blank=True,
        features=["bold", "italic", "link", "ol", "ul"],
    )

    max_count = 1
    parent_page_types = ["home.HomePage"]
    subpage_types = ["compagnie.MembrePage"]

    content_panels = Page.content_panels + [FieldPanel("body")]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context["membres"] = (
            MembrePage.objects.child_of(self).live().order_by("ordre")
        )
        return context

    class Meta:
        verbose_name = "Page compagnie"


class MembrePage(Page):
    """A single team member (/compagnie/<slug>/)."""

    role = models.CharField(max_length=255, blank=True)
    ordre = models.PositiveIntegerField("Ordre d'affichage", default=0)
    photo = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name="Photo",
    )
    description = RichTextField(blank=True)
    instagram = models.URLField("Lien Instagram", blank=True)
    portfolio = models.ForeignKey(
        "wagtaildocs.Document",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name="Portfolio (PDF)",
    )

    parent_page_types = ["compagnie.CompagniePage"]
    subpage_types = []

    content_panels = Page.content_panels + [
        MultiFieldPanel(
            [
                FieldPanel("role"),
                FieldPanel("ordre"),
            ],
            heading="Informations",
        ),
        FieldPanel("photo"),
        FieldPanel("description"),
        FieldPanel("instagram"),
        FieldPanel("portfolio"),
    ]

    search_fields = Page.search_fields + [
        index.SearchField("description"),
        index.SearchField("role"),
    ]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        parent = self.get_parent().specific
        context["membres"] = (
            MembrePage.objects.child_of(parent).live().order_by("ordre")
        )
        context["compagnie_page"] = parent
        return context

    class Meta:
        verbose_name = "Membre de l'équipe"
