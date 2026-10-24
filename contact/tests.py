"""Protection anti-bots (Cloudflare Turnstile) du formulaire de contact.

Règles métier :
- le widget n'est rendu que si TURNSTILE_SITE_KEY est configurée ;
- en POST, la soumission n'est traitée que si le jeton Turnstile est valide
  (vérification court-circuitée si TURNSTILE_SECRET_KEY est vide — dev/CI).
"""

from unittest import mock

from django.core import mail
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

    @mock.patch("contact.models.verify_turnstile", return_value=True)
    def test_client_ip_read_from_x_forwarded_for(self, mock_verify):
        # Derrière Traefik + nginx, REMOTE_ADDR est l'IP du proxy : c'est la
        # première IP de X-Forwarded-For qui doit être transmise à Cloudflare.
        self.client.post(
            self.form_page.url,
            {"message": "Bonjour", "cf-turnstile-response": "jeton"},
            HTTP_X_FORWARDED_FOR="203.0.113.7, 172.18.0.3",
        )

        mock_verify.assert_called_once_with("jeton", "203.0.113.7")


@override_settings(TURNSTILE_SECRET_KEY="")
class ContactFormEmailTests(WagtailPageTestCase):
    """Envoi par email des messages du formulaire de contact.

    Règles métier :
    - chaque soumission est envoyée à l'adresse (ou aux adresses) définie(s)
      par l'admin dans le champ « Adresse du destinataire » ;
    - le Reply-To est l'adresse email saisie par le visiteur ;
    - une panne SMTP ne fait pas échouer la soumission (déjà enregistrée).
    """

    def setUp(self):
        root_page = Page.get_first_root_node()
        Site.objects.create(hostname="testsite", root_page=root_page, is_default_site=True)
        homepage = HomePage(title="Home")
        root_page.add_child(instance=homepage)
        self.form_page = FormPage(
            title="Contact",
            thank_you_text="Merci !",
            to_address="contact@example.com, admin@example.com",
            from_address="site@example.com",
            subject="Nouveau message",
        )
        homepage.add_child(instance=self.form_page)
        FormField.objects.create(
            page=self.form_page, sort_order=0, label="Email",
            field_type="email", required=True,
        )
        FormField.objects.create(
            page=self.form_page, sort_order=1, label="Message",
            field_type="multiline", required=True,
        )

    def _post(self):
        return self.client.post(
            self.form_page.url,
            {"email": "visiteur@example.org", "message": "Bonjour la tribu"},
        )

    def test_submission_sends_email_to_admin_addresses(self):
        self._post()

        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(message.to, ["contact@example.com", "admin@example.com"])
        self.assertEqual(message.from_email, "site@example.com")
        self.assertEqual(message.subject, "Nouveau message")
        self.assertIn("Bonjour la tribu", message.body)

    def test_reply_to_is_visitor_email(self):
        self._post()

        self.assertEqual(mail.outbox[0].reply_to, ["visiteur@example.org"])

    def test_no_email_when_no_recipient(self):
        self.form_page.to_address = ""
        self.form_page.save()

        self._post()

        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(FormSubmission.objects.count(), 1)

    @mock.patch("contact.models.send_mail", side_effect=OSError("SMTP down"))
    def test_smtp_failure_does_not_break_submission(self, mock_send):
        with self.assertLogs("contact.models", level="ERROR"):
            response = self._post()

        self.assertContains(response, "Merci !")
        self.assertEqual(FormSubmission.objects.count(), 1)
