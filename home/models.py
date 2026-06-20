from wagtail.admin.panels import FieldPanel
from wagtail.fields import RichTextField
from wagtail.models import Page


class HomePage(Page):
    """Site root: full-screen carousel of stages + projets."""

    intro = RichTextField(
        "Texte de présentation (SEO)", blank=True,
        help_text="Texte de présentation lu par les moteurs de recherche.",
    )

    max_count = 1
    parent_page_types = ["wagtailcore.Page"]
    subpage_types = [
        "projets.ProjetIndexPage",
        "stages.StageIndexPage",
        "compagnie.CompagniePage",
        "reseaux.ReseauxPage",
    ]

    content_panels = Page.content_panels + [FieldPanel("intro")]

    def get_context(self, request, *args, **kwargs):
        from projets.models import ProjetPage
        from stages.models import StagePage

        context = super().get_context(request, *args, **kwargs)
        # Stages first, then projets — matching the legacy carousel order.
        context["carousel_stages"] = (
            StagePage.objects.live().order_by("ordre")
        )
        context["carousel_projets"] = (
            ProjetPage.objects.live().order_by("ordre")
        )
        return context

    class Meta:
        verbose_name = "Page d'accueil"
