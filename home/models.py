from django.db import models
from modelcluster.fields import ParentalKey
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel
from wagtail.fields import RichTextField, StreamField
from wagtail.models import Orderable, Page

from home.blocks import CustomSectionBlock


class HomePage(Page):
    """Site root: full-screen carousel of editable items."""

    intro = RichTextField(
        "Texte de présentation (SEO)", blank=True,
        help_text="Texte de présentation lu par les moteurs de recherche.",
    )
    custom_section = StreamField(
        CustomSectionBlock(),
        blank=True,
        verbose_name="Section personnalisable",
        help_text="Contenu libre affiché sous le carrousel.",
    )

    max_count = 1
    parent_page_types = ["wagtailcore.Page"]
    subpage_types = [
        "projets.ProjetIndexPage",
        "stages.StageIndexPage",
        "compagnie.CompagniePage",
        "reseaux.ReseauxPage",
        "contact.FormPage",
        "pros.ProPage",
    ]

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
        InlinePanel("carousel_items", label="Items du carrousel"),
        FieldPanel("custom_section"),
    ]

    def get_context(self, request, *args, **kwargs):
        from projets.models import ProjetPage
        from stages.models import StagePage

        context = super().get_context(request, *args, **kwargs)
        # Stages + projets restent exposés pour le bloc SEO (sr-only) uniquement.
        context["seo_stages"] = StagePage.objects.live().order_by("ordre")
        context["seo_projets"] = ProjetPage.objects.live().order_by("ordre")
        return context

    class Meta:
        verbose_name = "Page d'accueil"


class CarouselItem(Orderable):
    """Une diapositive du carrousel plein écran de la page d'accueil."""

    page = ParentalKey(
        HomePage, on_delete=models.CASCADE, related_name="carousel_items"
    )
    title = models.CharField("Titre", max_length=255)
    subtitle = models.CharField("Sous-titre", max_length=255, blank=True)
    description = RichTextField("Description", blank=True)
    background_image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=False,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name="Image de fond",
    )
    button_text = models.CharField(
        "Texte du bouton", max_length=100, blank=True, default="En savoir plus"
    )
    link_page = models.ForeignKey(
        "wagtailcore.Page",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name="Page liée par le bouton",
        help_text="Page du site vers laquelle pointe le bouton.",
    )

    panels = [
        FieldPanel("title"),
        FieldPanel("subtitle"),
        FieldPanel("description"),
        FieldPanel("background_image"),
        MultiFieldPanel(
            [FieldPanel("button_text"), FieldPanel("link_page")],
            heading="Bouton",
        ),
    ]

    class Meta(Orderable.Meta):
        verbose_name = "Item du carrousel"
        verbose_name_plural = "Items du carrousel"
