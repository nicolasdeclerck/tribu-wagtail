"""Page « Contact » basée sur le form builder natif de Wagtail
(`wagtail.contrib.forms`).

L'éditeur définit librement les champs du formulaire depuis l'admin (onglet
« Champs du formulaire »). Chaque soumission est enregistrée (consultable et
exportable dans l'admin) et envoyée par email aux adresses configurées.
"""

from django.db import models
from modelcluster.fields import ParentalKey
from wagtail.admin.panels import (
    FieldPanel,
    FieldRowPanel,
    InlinePanel,
    MultiFieldPanel,
)
from wagtail.contrib.forms.models import AbstractEmailForm, AbstractFormField
from wagtail.contrib.forms.panels import FormSubmissionsPanel
from wagtail.fields import RichTextField


class FormField(AbstractFormField):
    """Un champ du formulaire de contact (type, libellé, obligatoire…),
    ordonnable et édité en inline sur la `FormPage`."""

    page = ParentalKey(
        "FormPage", on_delete=models.CASCADE, related_name="form_fields"
    )


class FormPage(AbstractEmailForm):
    """Page de contact : formulaire configurable + envoi par email des réponses."""

    intro = RichTextField(
        "Texte d'introduction", blank=True,
        help_text="Affiché au-dessus du formulaire.",
    )
    thank_you_text = RichTextField(
        "Message de remerciement", blank=True,
        help_text="Affiché après l'envoi du formulaire.",
    )

    max_count = 1
    parent_page_types = ["home.HomePage"]
    subpage_types = []

    content_panels = AbstractEmailForm.content_panels + [
        FormSubmissionsPanel(),
        FieldPanel("intro"),
        InlinePanel("form_fields", label="Champs du formulaire"),
        FieldPanel("thank_you_text"),
        MultiFieldPanel(
            [
                FieldRowPanel(
                    [FieldPanel("from_address"), FieldPanel("to_address")]
                ),
                FieldPanel("subject"),
            ],
            heading="Envoi des réponses par email",
        ),
    ]

    class Meta:
        verbose_name = "Page de contact (formulaire)"
