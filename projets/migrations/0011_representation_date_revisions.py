"""Conversion des dates de représentation dans les révisions Wagtail.

La migration 0010 a converti le champ `date` en base, mais les révisions
(brouillons et historique) stockent une copie JSON de la page : elles contiennent
encore l'ancienne date en texte libre. Wagtail désérialise le dernier brouillon à
l'ouverture de l'éditeur, ce qui déclenchait une ValidationError
(« Le format de date de la valeur "19/09/2026" n'est pas valide »).
"""

from importlib import import_module

from django.db import migrations

parse_date = import_module(
    "projets.migrations.0010_representation_date_reelle"
).parse_date


def _convertir_contenu(contenu):
    """Réécrit en ISO les dates des représentations. Renvoie True si modifié."""
    representations = contenu.get("representations")
    if not isinstance(representations, list):
        return False

    modifie = False
    for representation in representations:
        if not isinstance(representation, dict):
            continue
        valeur = representation.get("date")
        if not isinstance(valeur, str):
            continue
        jour = parse_date(valeur)
        nouvelle = jour.isoformat() if jour else None
        if nouvelle != valeur:
            representation["date"] = nouvelle
            modifie = True
    return modifie


def convertir(apps, schema_editor):
    Revision = apps.get_model("wagtailcore", "Revision")
    ProjetPage = apps.get_model("projets", "ProjetPage")

    ids_projets = set(
        ProjetPage.objects.values_list("page_ptr_id", flat=True)
    )
    if not ids_projets:
        return

    a_sauver = []
    for revision in Revision.objects.iterator():
        contenu = revision.content
        if not isinstance(contenu, dict):
            continue
        if contenu.get("pk") not in ids_projets:
            continue
        if _convertir_contenu(contenu):
            revision.content = contenu
            a_sauver.append(revision)

    if a_sauver:
        Revision.objects.bulk_update(a_sauver, ["content"], batch_size=100)


class Migration(migrations.Migration):

    dependencies = [
        ("projets", "0010_representation_date_reelle"),
        ("wagtailcore", "0070_rename_pagerevision_revision"),
    ]

    # Pas de retour arrière : la migration 0010 réécrit déjà les dates en base,
    # et les révisions JSON ISO restent lisibles par l'ancien champ texte.
    operations = [migrations.RunPython(convertir, migrations.RunPython.noop)]
