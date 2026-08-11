from datetime import date
from urllib.parse import parse_qs, urlparse

from django.db import models
from django.utils import timezone
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

    def get_context(self, request, *args, **kwargs):
        from projets.structured_data import (
            breadcrumbs_dict,
            dumps_json_ld,
            theater_event_dict,
        )

        context = super().get_context(request, *args, **kwargs)
        context["structured_data"] = dumps_json_ld(
            [breadcrumbs_dict(request, self)]
            + [
                theater_event_dict(request, r)
                for r in self.representations_a_venir
                if r.date
            ]
        )
        return context

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
    def representations_a_venir(self):
        """Représentations pas encore jouées, de la plus proche à la plus lointaine.

        Les entrées sans date (héritage de l'ancien champ texte) sont conservées
        en fin de liste plutôt que masquées.
        """
        aujourdhui = timezone.localdate()
        reps = [
            r for r in self.representations.all()
            if r.date is None or r.date >= aujourdhui
        ]
        return sorted(
            reps, key=lambda r: (r.date is None, r.date or date.max, r.sort_order or 0)
        )

    @property
    def representations_passees(self):
        """Représentations déjà jouées, de la plus récente à la plus ancienne."""
        aujourdhui = timezone.localdate()
        reps = [
            r for r in self.representations.all()
            if r.date is not None and r.date < aujourdhui
        ]
        return sorted(reps, key=lambda r: r.date, reverse=True)

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
    """Une représentation du spectacle (date, horaire, lieu, billetterie).

    Le classement passé / à venir est automatique à partir de `date` : voir
    `ProjetPage.representations_a_venir` et `ProjetPage.representations_passees`.
    """

    page = ParentalKey(
        ProjetPage, on_delete=models.CASCADE, related_name="representations"
    )
    # null=True (et non blank=True) : la saisie reste obligatoire dans l'admin,
    # mais les entrées historiques dont la date en texte libre n'a pas pu être
    # convertie survivent à la migration sans être perdues.
    date = models.DateField("Date", null=True)
    horaire = models.CharField(max_length=255, blank=True)
    lieu = models.CharField(max_length=255, blank=True)
    detail = models.CharField(
        "Détail", max_length=255, blank=True,
        help_text="Précision affichée en petit sous le lieu "
                  "(ex. « Salle Jean Vilar », « Dans le cadre du festival… »).",
    )
    billetterie = models.URLField("Lien billetterie", blank=True)

    panels = [
        FieldPanel("date"),
        FieldPanel("horaire"),
        FieldPanel("lieu"),
        FieldPanel("detail"),
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
    photo_2 = models.ForeignKey(
        "wagtailimages.Image",
        verbose_name="Seconde photo",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Optionnelle : à renseigner si deux personnes se partagent le rôle. "
                  "Les deux photos s'affichent côte à côte.",
    )
    copyright_2 = models.CharField(
        "Copyright / crédit de la seconde photo", max_length=255, blank=True,
    )

    panels = [
        MultiFieldPanel(
            [FieldPanel("photo"), FieldPanel("copyright")],
            heading="Photo",
        ),
        MultiFieldPanel(
            [FieldPanel("photo_2"), FieldPanel("copyright_2")],
            heading="Seconde photo (rôle partagé)",
            classname="collapsed",
        ),
        FieldPanel("nom"),
        FieldPanel("role"),
    ]
