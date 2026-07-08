"""Page « Contact » basée sur le form builder natif de Wagtail
(`wagtail.contrib.forms`).

L'éditeur définit librement les champs du formulaire depuis l'admin (onglet
« Champs du formulaire »). Chaque soumission est enregistrée (consultable et
exportable dans l'admin) et envoyée par email aux adresses configurées.
"""

from django.db import models
from django.template.response import TemplateResponse
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

from core.turnstile import verify_turnstile


def _client_ip(request):
    """IP de l'appelant en tenant compte d'un éventuel proxy (X-Forwarded-For)."""
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


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

    def serve(self, request, *args, **kwargs):
        """Vérifie le jeton Cloudflare Turnstile avant de traiter la soumission.

        En cas d'échec (bot présumé, jeton absent ou invalide), le formulaire
        est ré-affiché avec une erreur globale et la soumission n'est ni
        enregistrée ni envoyée par email. Si `TURNSTILE_SECRET_KEY` n'est pas
        configurée, la vérification est désactivée (cf. core/turnstile.py).
        """
        if request.method == "POST":
            token = request.POST.get("cf-turnstile-response", "")
            if not verify_turnstile(token, _client_ip(request)):
                form = self.get_form(
                    request.POST, request.FILES, page=self, user=request.user
                )
                form.is_valid()  # déclenche full_clean, prérequis d'add_error
                form.add_error(
                    None,
                    "La vérification anti-robots a échoué. Merci de réessayer.",
                )
                context = self.get_context(request)
                context["form"] = form
                return TemplateResponse(request, self.get_template(request), context)
        return super().serve(request, *args, **kwargs)

    class Meta:
        verbose_name = "Page de contact (formulaire)"
