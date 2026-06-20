"""Seed the Wagtail page tree with the legacy "tribu d'Oya" content.

Idempotent: it can be run several times safely. Images and documents are
imported into the Wagtail library; pages are created (or updated) under the
HomePage.

    python manage.py seed_content
"""

from pathlib import Path

from django.conf import settings
from django.core.files.images import ImageFile
from django.core.files import File
from django.core.management.base import BaseCommand

from wagtail.documents import get_document_model
from wagtail.images import get_image_model
from wagtail.models import Page

from home.models import HomePage
from projets.models import ProjetIndexPage, ProjetPage, ProjetGalleryImage
from stages.models import (
    StageIndexPage,
    StagePage,
    StageObjectif,
    StageAxeTravail,
)
from compagnie.models import CompagniePage, MembrePage
from reseaux.models import ReseauxPage

Image = get_image_model()
Document = get_document_model()

IMG_DIR = Path(settings.PROJECT_DIR).parent / "core" / "static" / "img"
DOC_DIR = Path(settings.PROJECT_DIR).parent / "core" / "static" / "documents"


class Command(BaseCommand):
    help = "Seed the site with the legacy La tribu d'Oya content."

    def handle(self, *args, **options):
        self.stdout.write("Seeding content…")
        self.home = HomePage.objects.first()
        if self.home is None:
            self.stderr.write("No HomePage found — run migrations first.")
            return

        self.seed_home()
        # Order of creation drives the default menu order (native page tree order).
        self.seed_compagnie()
        self.seed_projets()
        self.seed_stages()
        self.seed_reseaux()
        self.stdout.write(self.style.SUCCESS("Done."))

    # ---- helpers -----------------------------------------------------------

    def get_image(self, filename, title=None):
        title = title or Path(filename).stem
        image = Image.objects.filter(title=title).first()
        if image:
            return image
        path = IMG_DIR / filename
        with path.open("rb") as fh:
            image = Image(title=title, file=ImageFile(fh, name=Path(filename).name))
            image.save()
        self.stdout.write(f"  + image {title}")
        return image

    def get_document(self, filename, title=None):
        title = title or Path(filename).stem
        doc = Document.objects.filter(title=title).first()
        if doc:
            return doc
        path = DOC_DIR / filename
        with path.open("rb") as fh:
            doc = Document(title=title, file=File(fh, name=Path(filename).name))
            doc.save()
        self.stdout.write(f"  + document {title}")
        return doc

    def upsert(self, parent, model, slug, fields):
        """Create or update a child page, returning the (saved) instance."""
        existing = parent.get_children().filter(slug=slug).first()
        if existing:
            page = existing.specific
            for key, value in fields.items():
                setattr(page, key, value)
            page.save()
        else:
            page = model(slug=slug, **fields)
            parent.add_child(instance=page)
        return page

    @staticmethod
    def publish(page):
        rev = page.save_revision()
        rev.publish()

    # ---- home --------------------------------------------------------------

    def seed_home(self):
        self.home.title = "Accueil"
        self.home.seo_title = "La tribu d'Oya - Compagnie de théâtre engagée"
        self.home.search_description = (
            "La tribu d'Oya est une compagnie de théâtre engagée créée en 2022. "
            "Découvrez nos spectacles engagés politiquement et socialement autour "
            "de l'égalité femmes-hommes et des droits des femmes."
        )
        self.home.intro = (
            "<p>La tribu d'Oya est une association de loi 1901 créée le 12 octobre "
            "2022. Ses spectacles ont l'ambition d'être engagés politiquement et "
            "socialement, notamment autour de la lutte pour l'égalité entre les "
            "femmes et les hommes et le respect des droits des femmes.</p>"
        )
        self.home.save()
        self.publish(self.home)

    # ---- projets -----------------------------------------------------------

    def seed_projets(self):
        index = self.upsert(
            self.home,
            ProjetIndexPage,
            "projets",
            {
                "title": "Les projets",
                "show_in_menus": True,
                "seo_title": "Nos projets - La tribu d'Oya | Spectacles de théâtre engagé",
                "search_description": (
                    "Découvrez nos spectacles de théâtre engagés : Olympe (2025) sur "
                    "Olympe de Gouges, Trafiquée (2023) sur les violences faites aux "
                    "femmes, et nos créations en cours."
                ),
            },
        )
        self.publish(index)

        trafiquee = self.upsert(
            index,
            ProjetPage,
            "trafiquee",
            {
                "title": "Trafiquée",
                "subtitle": "Pièce de théâtre",
                "annee": "2023",
                "ordre": 2,
                "is_in_progress": False,
                "background_image": self.get_image("trafiquee.png"),
                "credit": (
                    "<strong>Mise en scène</strong> : Stéphanie Horel<br />"
                    "<strong>Texte</strong> : Emma Haché<br />"
                    "<strong>Avec</strong> : Stéphanie Horel et Aude Sauvée"
                ),
                "description": (
                    "Trafiquée est un texte puissant sur les violences faites aux "
                    "femmes à travers le prisme de la prostitution. Le texte raconte "
                    "le parcours d'une femme comme tant d'autres, enlevée, vendue, "
                    "prostituée, trafiquée. Il y est aussi question d'espoir et de "
                    "résilience."
                ),
                "youtube_link": "https://www.youtube.com/embed/pu_PPp-4HQ8?si=EkI0h-y7m3hINCSG",
                "press_folder": self.get_document("dossier-de-presse-trafiquee.pdf"),
                "search_description": (
                    "Trafiquée (2023), pièce de théâtre sur les violences faites aux "
                    "femmes. Mise en scène Stéphanie Horel, texte Emma Haché."
                ),
            },
        )
        self.publish(trafiquee)

        olympe = self.upsert(
            index,
            ProjetPage,
            "olympe",
            {
                "title": "Olympe",
                "subtitle": "Pièce de théâtre",
                "annee": "2025",
                "ordre": 1,
                "is_in_progress": False,
                "background_image": self.get_image("olympe.png"),
                "credit": (
                    "<strong>Mise en scène</strong> : Stéphanie Horel<br />"
                    "<strong>Texte</strong> : Louis Domagala, Stephanie Horel, Aude Sauvée<br />"
                    "<strong>Avec</strong> : Lumîr Brabant, Romane Derrien, Félicie Honoré, "
                    "Stéphanie Horel et Aude Sauvée<br /><br />"
                    "<strong>Avec le soutien du <a href=\"https://www.collectifhfplushdf.com/\" "
                    "target=\"_blank\" rel=\"noopener noreferrer\">collectif HFX+</a></strong>"
                ),
                "description": (
                    "<p>A partir du texte: « La déclaration des droits de la femme et "
                    "de la citoyenne », 1791</p><p>Olympe de Gouges défendait le fait "
                    "que « si la femme a le droit de monter à l'échafaud, elle doit "
                    "aussi avoir celui de monter à la tribune ». Elle sera guillotinée "
                    "pour la défense de ses idées.</p>"
                ),
                "search_description": (
                    "Olympe (2025), pièce sur Olympe de Gouges et la Déclaration des "
                    "droits de la femme et de la citoyenne. Mise en scène Stéphanie Horel."
                ),
            },
        )
        olympe.gallery_images.clear()
        for i in range(1, 6):
            olympe.gallery_images.add(
                ProjetGalleryImage(image=self.get_image(f"olympe/olympe-{i}.png", f"olympe-{i}"))
            )
        olympe.save()
        self.publish(olympe)

        alors = self.upsert(
            index,
            ProjetPage,
            "alors-les-coeurs-se-tissent",
            {
                "title": "Alors les cœurs se tissent",
                "subtitle": "Pièce de théâtre",
                "annee": "En cours",
                "ordre": 3,
                "is_in_progress": True,
                "background_image": self.get_image("alors-les-coeurs-se-tissent.png"),
                "credit": (
                    "<strong>Mise en scène</strong> : Stéphanie Horel<br />"
                    "<strong>Texte</strong> : Veronika Boutinova<br />"
                    "<strong>Avec</strong> : Juliette Baron, Margeaux Lampley, Patrice Mendes"
                ),
                "description": "En cours de création",
                "search_description": "Alors les cœurs se tissent — création en cours.",
            },
        )
        self.publish(alors)

    # ---- stages ------------------------------------------------------------

    def seed_stages(self):
        index = self.upsert(
            self.home,
            StageIndexPage,
            "stages",
            {
                "title": "Les stages",
                "show_in_menus": True,
                "seo_title": "Les stages - La tribu d'Oya | Ateliers de théâtre",
                "search_description": (
                    "Découvrez nos stages de théâtre : Du JE au NOUS, une journée pour "
                    "explorer la puissance du collectif au féminin. Stages ouverts à "
                    "toutes les femmes, tous niveaux."
                ),
            },
        )
        self.publish(index)

        stage = self.upsert(
            index,
            StagePage,
            "choeur-de-femmes",
            {
                "title": "Chœur de femmes",
                "type": "Stage de théâtre",
                "subtitle": "Stage de théâtre",
                "ordre": 1,
                "background_image": self.get_image("stage-choeur-de-femmes.png"),
                "credit": "<strong>Animatrice :</strong> Stéphanie Horel",
                "description_courte": "La puissance du collectif au féminin",
                "intention": (
                    "<p>Cet atelier se veut un espace de recherche autour de la "
                    "dynamique de groupe, des énergies et des respirations collectives. "
                    "Un lieu d'exploration de la puissance féminine et du chœur de "
                    "femmes. Éprouver la force de l'unisson et la beauté de l'individu "
                    "au sein du groupe, conscientiser ce qui nous lie, ce qui nous agit "
                    "quand nous sommes ensemble.</p>"
                ),
                "theme": (
                    "<p>Passer du JE au NOUS : construire un chœur de femmes, trouver "
                    "l'unisson, explorer les dynamiques de groupe, les énergies "
                    "collectives. Se relier à l'autre, au groupe, par le souffle, le "
                    "regard, le mouvement, la voix.</p>"
                ),
                "note": (
                    "<p>Ce stage ne nécessite pas de niveau spécifique en théâtre. Il "
                    "s'adresse à toutes les femmes curieuses d'explorer la dynamique de "
                    "groupe et la puissance du collectif. Prévoir une tenue confortable.</p>"
                ),
                "youtube_link": "https://youtube.com/embed/s55NoxK9ifw",
                "search_description": (
                    "Stage « Du JE au NOUS » : une journée pour explorer la puissance "
                    "du collectif au féminin et le chœur de femmes."
                ),
            },
        )
        objectifs = [
            "Explorer le chœur de femmes comme outil de mise en scène",
            "Conscientiser les dynamiques de groupe",
            "Travailler l'écoute collective et l'unisson",
            "Découvrir la puissance du collectif au féminin",
        ]
        axes = [
            "Travail corporel et vocal",
            "Exercices d'écoute et de synchronisation",
            "Exploration des dynamiques de groupe",
            "Mise en pratique à travers des improvisations collectives",
        ]
        stage.objectifs.clear()
        for texte in objectifs:
            stage.objectifs.add(StageObjectif(texte=texte))
        stage.axes_travail.clear()
        for texte in axes:
            stage.axes_travail.add(StageAxeTravail(texte=texte))
        stage.save()
        self.publish(stage)

    # ---- compagnie ---------------------------------------------------------

    def seed_compagnie(self):
        index = self.upsert(
            self.home,
            CompagniePage,
            "compagnie",
            {
                "title": "La compagnie",
                "show_in_menus": True,
                "seo_title": "La compagnie - La tribu d'Oya | Association de théâtre féministe",
                "search_description": (
                    "La tribu d'Oya est une association de loi 1901 créée en 2022. "
                    "Découvrez notre équipe et notre mission : créer des spectacles "
                    "engagés autour de l'égalité femmes-hommes."
                ),
                "body": (
                    "<p>La tribu d'Oya est une association de loi 1901 créée le 12 "
                    "octobre 2022.</p>"
                    "<p>Ses spectacles ont l'ambition d'être engagés politiquement et "
                    "socialement : notamment autour de la lutte pour l'égalité entre "
                    "les femmes et les hommes et le respect des droits des femmes. La "
                    "tribu d'Oya souhaite ainsi participer entre autres à l'éducation "
                    "et la sensibilisation aux enjeux féminins et féministes au moyen "
                    "de la rencontre et de la transposition de ces questions au plateau "
                    "de théâtre.</p>"
                    "<p>D'autres thèmes contemporains de société pourront venir "
                    "s'ajouter à son champ de travail au cours de son développement.</p>"
                ),
            },
        )
        self.publish(index)

        membres = [
            {
                "slug": "stephanie",
                "title": "Stéphanie Horel",
                "role": "Directrice artistique / Metteuse en scène / Comédienne",
                "ordre": 1,
                "img": "equipe/stephanie.png",
                "instagram": "https://www.instagram.com/stephorel1973/",
                "portfolio": "portfolio-stephanie-horel.pdf",
                "description": (
                    "<p>Stéphanie est directrice artistique de la compagnie. Elle est "
                    "metteuse en scène et comédienne.</p><p>Elle a travaillé sous la "
                    "direction de Violaine Debarge, Daniela Piemontesi, Simon Capelle "
                    "et Antoine Lemaire en tant que comédienne.</p><p>Les textes "
                    "qu'elle aime mettre au plateau sont principalement ceux ayant pour "
                    "thèmes des sujets politiques et de sociétés (l'exil, les violences "
                    "faites aux femmes, l'émancipation des femmes, les jeux de "
                    "pouvoir…)</p>"
                ),
            },
            {
                "slug": "aude",
                "title": "Aude Sauvée",
                "role": "Comédienne",
                "ordre": 2,
                "img": "equipe/aude.png",
                "instagram": "https://www.instagram.com/audesv/",
                "portfolio": None,
                "description": (
                    "<p>Aude s'engage dans sa formation à travers plusieurs projets de "
                    "théâtre.</p><p>Elle intègre en 2021, la troupe Melting pÖt "
                    "(maelström théâtre), où elle y fait la rencontre de Stéphanie "
                    "Horel qui met en scène Migraaaants de Matéi Visniec, puis Gloriette "
                    "(d'après 'Chômage' du collectif Transquinquenal).</p><p>Aude "
                    "travaille en stage avec Eram Sobhani et Stéphane Auvray-Nauroy. "
                    "Elle se forme aussi auprès du metteur en scène argentin Guillermo "
                    "Cacace en 2023. S'en suivra la création de la pièce Trafiquée, mes "
                    "par Stéphanie Horel, avec qui elle partage la scène.</p><p>Elle "
                    "sera ensuite sous la direction de Violaine Debarge qui soutient un "
                    "travail sur la BeAT génération.</p>"
                ),
            },
            {
                "slug": "louis",
                "title": "Louis Domagala",
                "role": "Producteur",
                "ordre": 3,
                "img": "equipe/louis.png",
                "instagram": "https://www.instagram.com/loudodo/",
                "portfolio": None,
                "description": (
                    "<p>Louis est président de l'association Cultur'All depuis plus de "
                    "10 ans dont l'objet est la valorisation et la promotion des "
                    "cultures populaires.</p><p>Il écrit et produit des métrages "
                    "audiovisuels (documentaires, clips, fictions) ainsi que de "
                    "l'événementiel musical.</p><p>Comédien amateur, il s'intéresse à "
                    "la production théâtrale depuis 2022 et propose à Stéphanie Horel de "
                    "collaborer sur ses projets.</p><p>Il accompagne la tribu d'Oya "
                    "depuis sa création pour faciliter sa production. Il crée également "
                    "l'ensemble des parties audiovisuelles du spectacle Trafiquée "
                    "(teasers, captations, mapping).</p>"
                ),
            },
            {
                "slug": "nicolas",
                "title": "Nicolas Declerck",
                "role": "Compositeur",
                "ordre": 4,
                "img": "equipe/nicolas.png",
                "instagram": "https://www.instagram.com/ndeclerck/",
                "portfolio": None,
                "description": (
                    "<p>Nicolas commence le piano à l'âge de 4 ans avant d'approfondir "
                    "sa formation musicale au Conservatoire de Roubaix.</p><p>Au fil du "
                    "temps et des expériences variées (groupe de rock, orchestre…), sa "
                    "vocation se précise : Nicolas veut composer pour le spectacle "
                    "vivant et pour l'image.</p><p>En 2022, ce désir prend un tournant "
                    "fort avec la création de la musique de la pièce Trafiquée, en "
                    "collaboration avec Stéphanie Horel, metteuse en scène au sein de la "
                    "compagnie la tribu d'Oya.</p><p>Nicolas approfondit ses "
                    "connaissances au Conservatoire de Tourcoing et poursuit en "
                    "parallèle ses projets de création, seul ou en collaboration, avec "
                    "le désir constant d'innover en explorant de nouvelles textures et "
                    "en permettant la rencontre entre musique et dramaturgie pour "
                    "magnifier les récits artistiques.</p>"
                ),
            },
        ]
        for data in membres:
            fields = {
                "title": data["title"],
                "role": data["role"],
                "ordre": data["ordre"],
                "photo": self.get_image(data["img"], Path(data["img"]).stem),
                "instagram": data["instagram"] or "",
                "description": data["description"],
                "portfolio": self.get_document(data["portfolio"]) if data["portfolio"] else None,
                "search_description": f"{data['title']} — {data['role']}, La tribu d'Oya.",
            }
            membre = self.upsert(index, MembrePage, data["slug"], fields)
            self.publish(membre)

    # ---- reseaux -----------------------------------------------------------

    def seed_reseaux(self):
        page = self.upsert(
            self.home,
            ReseauxPage,
            "reseaux",
            {
                "title": "Suivre nos actus",
                "show_in_menus": True,
                "seo_title": "Nos réseaux sociaux - La tribu d'Oya | Facebook, Instagram",
                "search_description": (
                    "Suivez La tribu d'Oya sur les réseaux sociaux. Retrouvez-nous sur "
                    "Facebook, Instagram et Hello Asso pour suivre nos actualités."
                ),
                "newsletter_url": "https://docs.google.com/forms/d/e/1FAIpQLSewSgWZY9YDsHSC18c_kRbG-TqAj5YUsXkmHbkRxm8cYNgFUg/viewform?usp=header",
                "facebook_url": "https://www.facebook.com/latribudoya",
                "instagram_url": "https://www.instagram.com/latribudoya/",
                "helloasso_url": "https://www.helloasso.com/associations/la-tribu-d-oya",
            },
        )
        self.publish(page)
