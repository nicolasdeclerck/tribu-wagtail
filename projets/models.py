from urllib.parse import parse_qs, urlparse

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
    dossier_artistique_url = models.URLField(
        "Lien dossier artistique", blank=True,
        help_text="Lien externe vers le dossier artistique (affiché sous la "
        "description dans la bannière).",
    )
    youtube_link = models.URLField(
        "Lien YouTube", blank=True,
        help_text="Colle n'importe quel lien YouTube (youtu.be, watch?v=, "
        "shorts ou embed) : il est converti automatiquement pour l'intégration.",
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
    infos_complementaires = RichTextField(
        "Présentation du spectacle", blank=True,
        help_text="Texte de présentation affiché sous le teaser, dans la "
        "colonne principale de la page.",
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
        FieldPanel("dossier_artistique_url"),
        InlinePanel("representations", label="Prochaines représentations"),
        InlinePanel("acteurs", label="Distribution (acteur·rice·s)"),
        FieldPanel("youtube_link"),
        FieldPanel("press_folder"),
        InlinePanel("gallery_images", label="Galerie d'images"),
        FieldPanel("infos_complementaires"),
    ]

    search_fields = Page.search_fields + [
        index.SearchField("description"),
        index.SearchField("credit"),
        index.SearchField("infos_complementaires"),
    ]

    @property
    def has_detail_page(self):
        return not self.is_in_progress

    @property
    def youtube_embed_url(self):
        """Normalise n'importe quel lien YouTube (youtu.be, watch?v=, shorts,
        embed) en URL d'intégration utilisable dans une iframe."""
        url = (self.youtube_link or "").strip()
        if not url:
            return ""
        parsed = urlparse(url)
        host = parsed.netloc.lower()
        video_id = ""
        if "youtu.be" in host:
            video_id = parsed.path.lstrip("/").split("/")[0]
        elif "youtube.com" in host:
            if parsed.path.startswith("/embed/"):
                return url  # déjà un lien d'intégration
            if parsed.path == "/watch":
                video_id = parse_qs(parsed.query).get("v", [""])[0]
            elif parsed.path.startswith("/shorts/"):
                parts = parsed.path.split("/")
                video_id = parts[2] if len(parts) > 2 else ""
        if video_id:
            return f"https://www.youtube.com/embed/{video_id}"
        return url  # format non reconnu : on renvoie l'URL telle quelle

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


class ProjetRepresentation(Orderable):
    """Une prochaine représentation du spectacle (date, horaire, lieu, billetterie)."""

    page = ParentalKey(
        ProjetPage, on_delete=models.CASCADE, related_name="representations"
    )
    date = models.CharField(max_length=255)
    horaire = models.CharField(max_length=255, blank=True)
    lieu = models.CharField(max_length=255, blank=True)
    billetterie = models.URLField("Lien billetterie", blank=True)

    panels = [
        FieldPanel("date"),
        FieldPanel("horaire"),
        FieldPanel("lieu"),
        FieldPanel("billetterie"),
    ]


class ProjetActeur(Orderable):
    """Un·e acteur·rice de la distribution (photo + nom)."""

    page = ParentalKey(
        ProjetPage, on_delete=models.CASCADE, related_name="acteurs"
    )
    nom = models.CharField(max_length=255)
    role = models.CharField(
        "Rôle joué", max_length=255, blank=True,
        help_text="Affiché sous le nom dans la distribution.",
    )
    photo = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    copyright = models.CharField(
        "Copyright / crédit photo", max_length=255, blank=True,
        help_text="Affiché en surimpression de la photo (ex. « © Nom du photographe »).",
    )

    panels = [
        FieldPanel("photo"),
        FieldPanel("copyright"),
        FieldPanel("nom"),
        FieldPanel("role"),
    ]
