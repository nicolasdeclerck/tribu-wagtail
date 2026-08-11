from datetime import date, timedelta
from importlib import import_module

from django.utils import timezone
from wagtail.images import get_image_model
from wagtail.images.tests.utils import get_test_image_file
from wagtail.models import Page, Site
from wagtail.test.utils import WagtailPageTestCase

from home.models import HomePage
from projets.models import (
    ProjetActeur,
    ProjetGalleryImage,
    ProjetIndexPage,
    ProjetPage,
    ProjetRepresentation,
)

# Le nom des modules commence par un chiffre : import dynamique obligatoire.
parse_date = import_module(
    "projets.migrations.0010_representation_date_reelle"
).parse_date
convertir_contenu = import_module(
    "projets.migrations.0011_representation_date_revisions"
)._convertir_contenu


class RepresentationTriTests(WagtailPageTestCase):
    """Classement automatique des représentations en « à venir » / « passées »."""

    def setUp(self):
        root_page = Page.get_first_root_node()
        Site.objects.create(
            hostname="testsite", root_page=root_page, is_default_site=True
        )
        homepage = HomePage(title="Home")
        root_page.add_child(instance=homepage)
        index = ProjetIndexPage(title="Projets")
        homepage.add_child(instance=index)
        self.projet = ProjetPage(title="Mon spectacle")
        index.add_child(instance=self.projet)
        self.aujourdhui = timezone.localdate()

    def _rep(self, jours, **kwargs):
        return ProjetRepresentation.objects.create(
            page=self.projet,
            date=None if jours is None else self.aujourdhui + timedelta(days=jours),
            **kwargs,
        )

    def test_a_venir_de_la_plus_proche_a_la_plus_lointaine(self):
        lointaine = self._rep(30)
        proche = self._rep(2)
        self.assertEqual(
            list(self.projet.representations_a_venir), [proche, lointaine]
        )

    def test_passees_de_la_plus_recente_a_la_plus_ancienne(self):
        ancienne = self._rep(-90)
        recente = self._rep(-3)
        self.assertEqual(
            list(self.projet.representations_passees), [recente, ancienne]
        )

    def test_representation_du_jour_reste_a_venir(self):
        aujourdhui = self._rep(0)
        self.assertIn(aujourdhui, self.projet.representations_a_venir)
        self.assertNotIn(aujourdhui, self.projet.representations_passees)

    def test_representation_sans_date_reste_a_venir_en_fin_de_liste(self):
        sans_date = self._rep(None)
        datee = self._rep(10)
        self.assertEqual(
            list(self.projet.representations_a_venir), [datee, sans_date]
        )
        self.assertEqual(list(self.projet.representations_passees), [])

    def test_page_affiche_les_dernieres_representations_sans_billetterie(self):
        self._rep(-10, lieu="Théâtre d'hier", billetterie="https://ancien.example.com")
        response = self.client.get(self.projet.url)
        self.assertContains(response, "Dernières représentations")
        self.assertContains(response, "Théâtre d&#x27;hier")
        self.assertNotContains(response, "https://ancien.example.com")

    def test_section_dernieres_representations_absente_sans_passe(self):
        self._rep(10)
        response = self.client.get(self.projet.url)
        self.assertNotContains(response, "Dernières représentations")

    def test_bouton_voir_plus_seulement_au_dela_de_trois(self):
        for jours in range(1, 4):
            self._rep(-jours)
        response = self.client.get(self.projet.url)
        self.assertNotContains(response, "Voir plus")

        self._rep(-4)
        response = self.client.get(self.projet.url)
        self.assertContains(response, "Voir plus")

    def test_detail_affiche_sous_le_lieu(self):
        self._rep(5, lieu="Théâtre municipal", detail="Salle Jean Vilar")
        response = self.client.get(self.projet.url)
        self.assertContains(response, "Salle Jean Vilar")


class ParseDateMigrationTests(WagtailPageTestCase):
    """Conversion des anciennes dates en texte libre vers un vrai champ date."""

    def test_formats_numeriques(self):
        self.assertEqual(parse_date("19/09/2026"), date(2026, 9, 19))
        self.assertEqual(parse_date("19-09-2026"), date(2026, 9, 19))
        self.assertEqual(parse_date("19.09.26"), date(2026, 9, 19))
        self.assertEqual(parse_date("2026-09-19"), date(2026, 9, 19))

    def test_dates_en_toutes_lettres(self):
        self.assertEqual(parse_date("19 septembre 2026"), date(2026, 9, 19))
        self.assertEqual(parse_date("samedi 19 sept. 2026"), date(2026, 9, 19))
        self.assertEqual(parse_date("1er août 2026"), date(2026, 8, 1))
        self.assertEqual(parse_date("12 Décembre 2025"), date(2025, 12, 12))

    def test_date_reconnue_dans_une_saisie_multiple(self):
        self.assertEqual(parse_date("19 et 20 septembre 2026"), date(2026, 9, 20))

    def test_valeurs_non_reconnues(self):
        self.assertIsNone(parse_date(""))
        self.assertIsNone(parse_date("prochainement"))
        self.assertIsNone(parse_date("31/02/2026"))


class ConversionRevisionsTests(WagtailPageTestCase):
    """Réécriture des dates dans la copie JSON des pages (révisions Wagtail).

    Sans elle, ouvrir la page dans l'admin lève une ValidationError : Wagtail
    désérialise le dernier brouillon, qui contient encore l'ancien texte.
    """

    def test_dates_converties_en_iso(self):
        contenu = {"representations": [{"date": "19/09/2026"}, {"date": "1er août 2026"}]}
        self.assertTrue(convertir_contenu(contenu))
        self.assertEqual(
            [r["date"] for r in contenu["representations"]],
            ["2026-09-19", "2026-08-01"],
        )

    def test_date_non_reconnue_mise_a_null(self):
        contenu = {"representations": [{"date": "prochainement"}]}
        self.assertTrue(convertir_contenu(contenu))
        self.assertIsNone(contenu["representations"][0]["date"])

    def test_idempotent_sur_une_date_deja_iso(self):
        contenu = {"representations": [{"date": "2026-09-19"}]}
        self.assertFalse(convertir_contenu(contenu))
        self.assertEqual(contenu["representations"][0]["date"], "2026-09-19")

    def test_contenu_sans_representations_ignore(self):
        self.assertFalse(convertir_contenu({"title": "Une page"}))
        self.assertFalse(convertir_contenu({"representations": None}))


class GalerieAltTextTests(WagtailPageTestCase):
    """Textes alternatifs SEO/accessibilité des images de galerie."""

    def setUp(self):
        root_page = Page.get_first_root_node()
        Site.objects.create(
            hostname="testsite", root_page=root_page, is_default_site=True
        )
        homepage = HomePage(title="Home")
        root_page.add_child(instance=homepage)
        index = ProjetIndexPage(title="Projets")
        homepage.add_child(instance=index)
        self.projet = ProjetPage(title="Olympe", annee="2025")
        index.add_child(instance=self.projet)

        Image = get_image_model()
        self.image = Image(title="olympe-1", file=get_test_image_file())
        self.image.save()
        self.galerie = ProjetGalleryImage.objects.create(
            page=self.projet, image=self.image
        )

    def test_alt_slider_contient_spectacle_et_annee(self):
        response = self.client.get(self.projet.url)
        self.assertContains(
            response, 'alt="Affiche du spectacle Olympe — création 2025"'
        )

    def test_alt_miniature_contient_spectacle_annee_et_photo(self):
        response = self.client.get(self.projet.url)
        self.assertContains(
            response, 'alt="Affiche du spectacle Olympe — création 2025 — photo 1"'
        )

    def test_alt_sans_annee_omet_creation(self):
        self.projet.annee = ""
        self.projet.save()
        response = self.client.get(self.projet.url)
        self.assertContains(
            response, 'alt="Affiche du spectacle Olympe"'
        )
        self.assertNotContains(response, "création")

    def test_alt_priorite_a_la_description_de_l_image(self):
        self.image.description = "Photo de scène d'Olympe"
        self.image.save()
        response = self.client.get(self.projet.url)
        self.assertContains(response, 'alt="Photo de scène d&#x27;Olympe"')

    def test_alt_acteurs_inchange(self):
        acteur = ProjetActeur.objects.create(
            page=self.projet, nom="Stéphanie Horel", role="Mise en scène"
        )
        acteur.photo = self.image
        acteur.save()
        response = self.client.get(self.projet.url)
        self.assertContains(response, 'alt="Stéphanie Horel"')
