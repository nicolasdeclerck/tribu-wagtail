from django.db import models
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.models import Page


class ReseauxPage(Page):
    """The "Suivre nos actus" page (/reseaux/)."""

    newsletter_url = models.URLField(
        "Lien newsletter", blank=True,
        default="https://docs.google.com/forms/d/e/1FAIpQLSewSgWZY9YDsHSC18c_kRbG-TqAj5YUsXkmHbkRxm8cYNgFUg/viewform?usp=header",
    )
    facebook_url = models.URLField(
        "Lien Facebook", blank=True, default="https://www.facebook.com/latribudoya"
    )
    instagram_url = models.URLField(
        "Lien Instagram", blank=True, default="https://www.instagram.com/latribudoya/"
    )
    helloasso_url = models.URLField(
        "Lien HelloAsso", blank=True,
        default="https://www.helloasso.com/associations/la-tribu-d-oya",
    )

    max_count = 1
    parent_page_types = ["home.HomePage"]
    subpage_types = []

    content_panels = Page.content_panels + [
        MultiFieldPanel(
            [
                FieldPanel("newsletter_url"),
                FieldPanel("facebook_url"),
                FieldPanel("instagram_url"),
                FieldPanel("helloasso_url"),
            ],
            heading="Liens",
        ),
    ]

    class Meta:
        verbose_name = "Page réseaux sociaux"
