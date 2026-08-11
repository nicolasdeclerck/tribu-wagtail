from datetime import date, time, timedelta
from importlib import import_module

from django.apps import apps
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
from projets.structured_data import parse_horaire

# Le nom des modules commence par un chiffre : import dynamique obligatoire.
parse_date = import_module(
    "projets.migrations.0010_representation_date_reelle"
).parse_date
convertir_contenu = import_module(
    "projets.migrations.0011_representation_date_revisions"
)._convertir_contenu
migration_meta = import_module(
    "projets.migrations.0012_remplir_search_description"
)


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


class TheaterEventJsonLdTests(WagtailPageTestCase):
    """JSON-LD schema.org TheaterEvent sur les pages spectacle et l'accueil."""

    def setUp(self):
        root_page = Page.get_first_root_node()
        Site.objects.create(
            hostname="testsite", root_page=root_page, is_default_site=True
        )
        self.home = HomePage(title="Home")
        root_page.add_child(instance=self.home)
        index = ProjetIndexPage(title="Projets")
        self.home.add_child(instance=index)
        self.projet = ProjetPage(title="Mon spectacle")
        index.add_child(instance=self.projet)
        self.aujourdhui = timezone.localdate()

    def _rep(self, jours, **kwargs):
        return ProjetRepresentation.objects.create(
            page=self.projet,
            date=None if jours is None else self.aujourdhui + timedelta(days=jours),
            **kwargs,
        )

    def test_parse_horaire(self):
        self.assertEqual(parse_horaire("20h"), time(20, 0))
        self.assertEqual(parse_horaire("20h30"), time(20, 30))
        self.assertEqual(parse_horaire("20:30"), time(20, 30))
        self.assertEqual(parse_horaire("20 h 30"), time(20, 30))
        self.assertIsNone(parse_horaire(""))
        self.assertIsNone(parse_horaire("soirée"))
        self.assertIsNone(parse_horaire("25h"))

    def test_jsonld_theater_event_sur_page_spectacle(self):
        self._rep(
            10,
            lieu="Bazaar Saint So - 292 rue Camille Guérin, 59000 Lille",
            horaire="20h30",
            billetterie="https://billets.example.com",
        )
        response = self.client.get(self.projet.url)
        self.assertContains(response, '"@type": "TheaterEvent"')
        self.assertContains(
            response,
            "Mon spectacle — Bazaar Saint So - 292 rue Camille Guérin, 59000 Lille",
        )
        self.assertContains(response, "T20:30:00")
        self.assertContains(response, '"eventStatus"')
        self.assertContains(response, '"Bazaar Saint So"')
        self.assertContains(response, "292 rue Camille Guérin")
        self.assertContains(response, '"59000"')
        self.assertContains(response, '"Lille"')
        self.assertContains(response, "https://billets.example.com")
        self.assertContains(response, '"@type": "BreadcrumbList"')

    def test_jsonld_exclut_sans_date_et_passees(self):
        self._rep(None)
        self._rep(-10)
        response = self.client.get(self.projet.url)
        self.assertContains(response, '"@type": "BreadcrumbList"')
        self.assertNotContains(response, '"@type": "TheaterEvent"')

    def test_jsonld_pas_de_theater_event_sans_representation(self):
        response = self.client.get(self.projet.url)
        self.assertNotContains(response, '"@type": "TheaterEvent"')

    def test_jsonld_accueil(self):
        self._rep(
            10,
            lieu="Jardin de la maison des jeunes, 31 rue Jules Guesde, 59000 Lille",
            horaire="17h",
        )
        response = self.client.get(self.home.url)
        self.assertContains(response, '"@type": "PerformingGroup"')
        self.assertContains(response, '"La tribu d\'Oya"')
        self.assertContains(response, '"@type": "TheaterEvent"')
        self.assertContains(response, "T17:00:00")
        self.assertContains(response, "31 rue Jules Guesde")

        # Une représentation passée ne doit pas apparaître dans le JSON-LD.
        self._rep(-10)
        response = self.client.get(self.home.url)
        self.assertNotContains(
            response, (self.aujourdhui - timedelta(days=10)).isoformat()
        )


class MetaDescriptionTests(WagtailPageTestCase):
    """Meta description garantie sur les pages spectacle.

    base.html ne rend la balise que si `search_description` est renseigné :
    ProjetPage.save() génère donc un fallback depuis le contenu de la page
    quand le champ (onglet « Promotion ») est laissé vide, et la migration
    0012 rattrape les pages existantes (ex. /projets/jeanne-chauvin/).
    """

    def setUp(self):
        root_page = Page.get_first_root_node()
        Site.objects.create(
            hostname="testsite", root_page=root_page, is_default_site=True
        )
        homepage = HomePage(title="Home")
        root_page.add_child(instance=homepage)
        self.index = ProjetIndexPage(title="Projets")
        homepage.add_child(instance=self.index)

    def _projet(self, **kwargs):
        projet = ProjetPage(title="Mon spectacle", **kwargs)
        self.index.add_child(instance=projet)
        return projet

    def test_save_genere_un_fallback_depuis_infos_complementaires(self):
        projet = self._projet(
            infos_complementaires="<p>Un spectacle engagé sur les femmes.</p>"
        )
        self.assertEqual(
            projet.search_description, "Un spectacle engagé sur les femmes."
        )

    def test_save_fallback_depuis_description_si_pas_de_presentation(self):
        projet = self._projet(description="<p>Seule une description existe.</p>")
        self.assertEqual(projet.search_description, "Seule une description existe.")

    def test_save_fallback_tronque_a_155_caracteres(self):
        projet = self._projet(description="<p>" + "mot " * 80 + "</p>")
        self.assertLessEqual(len(projet.search_description), 155)

    def test_save_ne_ecrase_pas_une_description_existante(self):
        projet = self._projet(
            search_description="Description écrite à la main",
            description="<p>Contenu de la page.</p>",
        )
        self.assertEqual(projet.search_description, "Description écrite à la main")

    def test_save_sans_contenu_ne_cree_pas_de_description_vide(self):
        # fallback impossible : le champ reste vide plutôt qu'une chaîne vide
        # qui écraserait un éventuel remplissage ultérieur.
        projet = self._projet()
        self.assertEqual(projet.search_description, "")

    def test_rendu_contient_meta_description_non_vide(self):
        projet = self._projet(
            infos_complementaires="<p>La première avocate française.</p>"
        )
        response = self.client.get(projet.url)
        self.assertContains(
            response, '<meta name="description" content="La première avocate française." />'
        )

    def test_migration_remplit_jeanne_chauvin(self):
        projet = self._projet(
            slug="jeanne-chauvin",
            description="<p>Contenu existant.</p>",
        )
        # Simule l'état en production : page créée avant le fallback, champ vide.
        ProjetPage.objects.filter(pk=projet.pk).update(search_description="")
        migration_meta.remplir(apps, None)
        projet.refresh_from_db()
        self.assertEqual(
            projet.search_description,
            migration_meta.DESCRIPTION_JEANNE_CHAUVIN,
        )

    def test_migration_fallback_pour_les_autres_pages_sans_description(self):
        projet = self._projet(
            slug="autre-spectacle",
            description="<p>Un autre spectacle sans description courte.</p>",
        )
        ProjetPage.objects.filter(pk=projet.pk).update(search_description="")
        migration_meta.remplir(apps, None)
        projet.refresh_from_db()
        self.assertEqual(
            projet.search_description, "Un autre spectacle sans description courte."
        )

    def test_migration_ne_touche_pas_les_pages_remplies(self):
        projet = self._projet(search_description="Déjà renseignée")
        migration_meta.remplir(apps, None)
        projet.refresh_from_db()
        self.assertEqual(projet.search_description, "Déjà renseignée")

    def test_fallback_tronque_comme_le_modele(self):
        # La migration duplique la logique du modèle : les deux doivent produire
        # le même résultat pour un contenu donné.
        contenu = "<p>" + "phrase " * 60 + "</p>"
        projet = self._projet(description=contenu)
        self.assertEqual(
            projet.search_description, migration_meta.fallback(projet)
        )


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
