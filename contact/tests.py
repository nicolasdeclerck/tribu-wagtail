"""Protection anti-bots (Cloudflare Turnstile) du formulaire de contact.

Règles métier :
- le widget n'est rendu que si TURNSTILE_SITE_KEY est configurée ;
- en POST, la soumission n'est traitée que si le jeton Turnstile est valide
  (vérification court-circuitée si TURNSTILE_SECRET_KEY est vide — dev/CI).
"""

from unittest import mock

from django.test import override_settings

from wagtail.contrib.forms.models import FormSubmission
from wagtail.models import Page, Site
from wagtail.test.utils import WagtailPageTestCase

from contact.models import FormField, FormPage
from home.models import HomePage

SITE_KEY = "0x4AAAAAAA-site-key-test"


class TurnstileContactFormTests(WagtailPageTestCase):
    def setUp(self):
        root_page = Page.get_first_root_node()
        Site.objects.create(hostname="testsite", root_page=root_page, is_default_site=True)
        homepage = HomePage(title="Home")
        root_page.add_child(instance=homepage)
        self.form_page = FormPage(title="Contact", thank_you_text="Merci !")
        homepage.add_child(instance=self.form_page)
        FormField.objects.create(
            page=self.form_page, label="Message", field_type="multiline", required=True
        )

    def _post(self, **extra):
        return self.client.post(self.form_page.url, {"message": "Bonjour", **extra})

    @override_settings(TURNSTILE_SITE_KEY="")
    def test_widget_not_rendered_when_unconfigured(self):
        body = self.client.get(self.form_page.url).content.decode()

        self.assertNotIn("cf-turnstile", body)
        self.assertNotIn("challenges.cloudflare.com", body)

    @override_settings(TURNSTILE_SITE_KEY=SITE_KEY)
    def test_widget_rendered_when_configured(self):
        body = self.client.get(self.form_page.url).content.decode()

        self.assertIn(f'data-sitekey="{SITE_KEY}"', body)
        self.assertIn("challenges.cloudflare.com/turnstile/v0/api.js", body)

    @override_settings(TURNSTILE_SECRET_KEY="")
    def test_submission_accepted_when_verification_disabled(self):
        response = self._post()

        # Vérification désactivée (pas de clé) → soumission traitée normalement.
        self.assertContains(response, "Merci !")
        self.assertEqual(FormSubmission.objects.count(), 1)

    @mock.patch("contact.models.verify_turnstile", return_value=False)
    def test_submission_rejected_when_token_invalid(self, mock_verify):
        response = self._post(**{"cf-turnstile-response": "jeton-bidon"})

        # Bot présumé → formulaire ré-affiché avec l'erreur, rien d'enregistré.
        self.assertContains(response, "La vérification anti-robots a échoué")
        self.assertEqual(FormSubmission.objects.count(), 0)

    @mock.patch("contact.models.verify_turnstile", return_value=True)
    def test_submission_accepted_when_token_valid(self, mock_verify):
        response = self._post(**{"cf-turnstile-response": "jeton-valide"})

        self.assertContains(response, "Merci !")
        self.assertEqual(FormSubmission.objects.count(), 1)
        mock_verify.assert_called_once()
