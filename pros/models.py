import json

from django.db import models
from django.utils.html import strip_tags
from django.utils.text import Truncator
from modelcluster.fields import ParentalKey
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel
from wagtail.fields import RichTextField
from wagtail.models import Orderable, Page
from wagtail.search import index


class ProPage(Page):
    """Page dédiée aux professionnel·le·s (programmateur·ice·s) —
    /programmer-un-spectacle/. Optimisée pour le référencement : contenu
    éditable, liste des spectacles générée depuis l'arbre de pages et
    données structurées schema.org."""

    accroche = models.CharField(
        "Accroche", max_length=255, blank=True,
        help_text="Affichée sous le titre dans la bannière, en capitales.",
    )
    background_image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name="Image de fond",
    )
    intro = RichTextField(
        "Introduction", blank=True,
        help_text="Pitch de la compagnie à destination des "
        "programmateur·ice·s, affiché sous la bannière.",
    )
    atouts_titre = models.CharField(
        "Titre de la section atouts", max_length=255,
        default="Pourquoi programmer la tribu d'Oya ?",
    )
    spectacles_titre = models.CharField(
        "Titre de la section spectacles", max_length=255,
        default="Nos spectacles disponibles à la programmation",
    )
    infos_pratiques = RichTextField(
        "Informations pratiques", blank=True,
        help_text="Conditions d'accueil, fiche technique, jauge, tarifs… "
        "Affiché après la liste des spectacles.",
    )
    cta_titre = models.CharField(
        "Titre de l'appel à contact", max_length=255,
        default="Vous souhaitez programmer l'un de nos spectacles ?",
    )
    cta_texte = RichTextField(
        "Texte de l'appel à contact", blank=True,
        help_text="Affiché sous le titre, au-dessus du bouton vers la "
        "page contact.",
    )

    max_count = 1
    parent_page_types = ["home.HomePage"]
    subpage_types = []

    content_panels = Page.content_panels + [
        MultiFieldPanel(
            [
                FieldPanel("accroche"),
                FieldPanel("background_image"),
            ],
            heading="Bannière",
        ),
        FieldPanel("intro"),
        FieldPanel("atouts_titre"),
        InlinePanel("atouts", label="Atouts (pourquoi nous programmer)"),
        FieldPanel("spectacles_titre"),
        FieldPanel("infos_pratiques"),
        MultiFieldPanel(
            [
                FieldPanel("cta_titre"),
                FieldPanel("cta_texte"),
            ],
            heading="Appel à contact",
        ),
    ]

    search_fields = Page.search_fields + [
        index.SearchField("intro"),
        index.SearchField("infos_pratiques"),
    ]

    def get_context(self, request, *args, **kwargs):
        from projets.models import ProjetPage

        context = super().get_context(request, *args, **kwargs)
        spectacles = (
            ProjetPage.objects.live()
            .filter(is_in_progress=False)
            .order_by("ordre")
        )
        context["spectacles"] = spectacles
        context["structured_data"] = self._structured_data(request, spectacles)
        return context

    def _structured_data(self, request, spectacles):
        """JSON-LD schema.org : la compagnie (PerformingGroup) et la liste
        de ses spectacles, pour les résultats enrichis des moteurs."""
        items = []
        for position, spectacle in enumerate(spectacles, start=1):
            work = {
                "@type": "CreativeWork",
                "name": spectacle.title,
                "url": request.build_absolute_uri(spectacle.url),
            }
            if spectacle.description:
                work["description"] = Truncator(
                    strip_tags(spectacle.description)
                ).chars(300)
            if spectacle.background_image:
                rendition = spectacle.background_image.get_rendition("width-1200")
                work["image"] = request.build_absolute_uri(rendition.url)
            items.append(
                {"@type": "ListItem", "position": position, "item": work}
            )
        data = [
            {
                "@context": "https://schema.org",
                "@type": "PerformingGroup",
                "name": "La tribu d'Oya",
                "url": request.build_absolute_uri("/"),
                "description": Truncator(
                    strip_tags(self.intro or self.search_description or "")
                ).chars(300),
            },
            {
                "@context": "https://schema.org",
                "@type": "ItemList",
                "name": self.spectacles_titre,
                "itemListElement": items,
            },
        ]
        # « </ » échappé pour ne pas pouvoir fermer la balise <script>.
        return json.dumps(data, ensure_ascii=False).replace("</", "<\\/")

    class Meta:
        verbose_name = "Page professionnels"


class ProAtout(Orderable):
    """Un argument à destination des programmateur·ice·s (titre + texte)."""

    page = ParentalKey(
        ProPage, on_delete=models.CASCADE, related_name="atouts"
    )
    titre = models.CharField("Titre", max_length=255)
    texte = models.TextField("Texte", blank=True)

    panels = [
        FieldPanel("titre"),
        FieldPanel("texte"),
    ]
