"""Meta descriptions manquantes sur les pages spectacle.

L'audit SEO (t_6b888557) a relevé que /projets/jeanne-chauvin/ n'avait aucune
<meta name="description"> : le champ natif `search_description` (onglet
« Promotion » de l'admin) n'est pas forcé par ProjetPage, et les pages créées
sans lui ne sont couvertes par aucun fallback.

Cette migration remplit une seule fois le champ pour les pages existantes :
- Jeanne Chauvin reçoit la description rédigée lors de l'audit ;
- les autres pages sans description reçoivent un fallback généré depuis leur
  contenu (même logique que ProjetPage._fallback_search_description, dupliquée
  ici car les migrations doivent rester autonomes).

Les pages qui ont déjà une search_description ne sont pas touchées.
"""

from django.db import migrations
from django.utils.html import strip_tags
from django.utils.text import Truncator

MAX_LENGTH = 155

DESCRIPTION_JEANNE_CHAUVIN = (
    "Spectacle Jeanne Chauvin — l'histoire de la première avocate française, "
    "entre combat féministe et théâtre. Création de La tribu d'Oya (Lille), "
    "disponible à la programmation."
)


def fallback(projet):
    """Meta description générée depuis le contenu de la page (≈155 caractères)."""
    source = (projet.infos_complementaires or "").strip() or (projet.description or "").strip()
    texte = " ".join(strip_tags(source).split())
    return Truncator(texte).chars(MAX_LENGTH, truncate="…") if texte else ""


def remplir(apps, schema_editor):
    ProjetPage = apps.get_model("projets", "ProjetPage")
    projets = ProjetPage.objects.filter(search_description="").only(
        "slug", "description", "infos_complementaires"
    )
    a_sauver = []
    for projet in projets:
        if projet.slug == "jeanne-chauvin":
            projet.search_description = DESCRIPTION_JEANNE_CHAUVIN
        else:
            projet.search_description = fallback(projet)
        a_sauver.append(projet)
    if a_sauver:
        ProjetPage.objects.bulk_update(a_sauver, ["search_description"])


class Migration(migrations.Migration):

    dependencies = [
        ("projets", "0011_representation_date_revisions"),
    ]

    # Pas de retour arrière : on ne peut pas distinguer les descriptions écrites
    # ici de celles saisies à la main (elles sont identiques une fois en base).
    operations = [migrations.RunPython(remplir, migrations.RunPython.noop)]
