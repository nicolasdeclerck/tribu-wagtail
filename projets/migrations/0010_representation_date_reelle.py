"""Passage du champ `date` des représentations d'un texte libre à une vraie date.

Une vraie date est nécessaire pour classer automatiquement les représentations
en « à venir » / « passées ». Les valeurs existantes sont converties au mieux
(formats numériques et dates en toutes lettres en français) ; celles qui ne sont
pas reconnues restent nulles et sont traitées comme « à venir » côté site.
"""

import datetime
import re

from django.db import migrations, models

MOIS = {
    "janvier": 1, "janv": 1, "jan": 1,
    "fevrier": 2, "fevr": 2, "fev": 2,
    "mars": 3,
    "avril": 4, "avr": 4,
    "mai": 5,
    "juin": 6,
    "juillet": 7, "juil": 7,
    "aout": 8,
    "septembre": 9, "sept": 9, "sep": 9,
    "octobre": 10, "oct": 10,
    "novembre": 11, "nov": 11,
    "decembre": 12, "dec": 12,
}

ACCENTS = str.maketrans("àâäéèêëîïôöùûüç", "aaaeeeeiioouuuc")

# 19/09/2026, 19-09-2026, 19.09.26
NUMERIQUE = re.compile(r"\b(\d{1,2})[/.-](\d{1,2})[/.-](\d{2,4})\b")
# 2026-09-19
ISO = re.compile(r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b")
# « 19 septembre 2026 », « samedi 19 sept. 2026 ». Sur une plage du type
# « 19 et 20 septembre 2026 », seule « 20 septembre 2026 » est complète : c'est
# elle qui est retenue.
LETTRES = re.compile(r"\b(\d{1,2})\s*(?:er)?\s+([a-z]+)\.?\s+(\d{4})\b")


def parse_date(texte):
    """Renvoie une `date` à partir d'une saisie libre, ou None si non reconnue."""
    if not texte:
        return None
    brut = texte.strip().lower().translate(ACCENTS)

    match = ISO.search(brut)
    if match:
        annee, mois, jour = (int(g) for g in match.groups())
        return _construire(annee, mois, jour)

    match = NUMERIQUE.search(brut)
    if match:
        jour, mois, annee = (int(g) for g in match.groups())
        if annee < 100:  # année sur deux chiffres
            annee += 2000
        return _construire(annee, mois, jour)

    match = LETTRES.search(brut)
    if match:
        jour, nom_mois, annee = match.group(1), match.group(2), match.group(3)
        mois = MOIS.get(nom_mois)
        if mois:
            return _construire(int(annee), mois, int(jour))

    return None


def _construire(annee, mois, jour):
    try:
        return datetime.date(annee, mois, jour)
    except ValueError:  # 31/02, mois hors bornes…
        return None


def convertir(apps, schema_editor):
    Representation = apps.get_model("projets", "ProjetRepresentation")
    for rep in Representation.objects.all():
        jour = parse_date(rep.date)
        if jour is not None:
            rep.date_jour = jour
            rep.save(update_fields=["date_jour"])


def revenir(apps, schema_editor):
    """Retour arrière : on réécrit la date au format jj/mm/aaaa."""
    Representation = apps.get_model("projets", "ProjetRepresentation")
    for rep in Representation.objects.all():
        rep.date_jour = rep.date.strftime("%d/%m/%Y") if rep.date else ""
        rep.save(update_fields=["date_jour"])


class Migration(migrations.Migration):

    dependencies = [
        ("projets", "0009_projetacteur_copyright_2_projetacteur_photo_2"),
    ]

    operations = [
        migrations.AddField(
            model_name="projetrepresentation",
            name="date_jour",
            field=models.DateField(null=True, verbose_name="Date"),
        ),
        migrations.RunPython(convertir, revenir),
        migrations.RemoveField(model_name="projetrepresentation", name="date"),
        migrations.RenameField(
            model_name="projetrepresentation",
            old_name="date_jour",
            new_name="date",
        ),
        migrations.AddField(
            model_name="projetrepresentation",
            name="detail",
            field=models.CharField(
                blank=True,
                help_text="Précision affichée en petit sous le lieu "
                          "(ex. « Salle Jean Vilar », « Dans le cadre du festival… »).",
                max_length=255,
                verbose_name="Détail",
            ),
        ),
    ]
