from django.db import migrations


def fix_site_hostname(apps, schema_editor):
    """Corrige le hostname de l'enregistrement Wagtail Site.

    En production, l'enregistrement Site pointait vers un hôte interne
    (``latribudoya`` ou ``localhost``) : ``Page.full_url`` générait alors des
    URLs ``http://latribudoya/...``, reprises telles quelles dans le canonical
    et og:url (cf. issue #12). On force l'hostname public + port 443
    (→ root_url ``https://latribudoya.fr``).
    """
    Site = apps.get_model("wagtailcore.Site")
    Site.objects.filter(hostname__in=["latribudoya", "localhost"]).update(
        hostname="latribudoya.fr", port=443, is_default_site=True
    )


def reverse_fix_site_hostname(apps, schema_editor):
    # Le hostname d'origine dépend de l'environnement (localhost en dev) :
    # rien de fiable à restaurer.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0007_alter_homepage_custom_section"),
    ]

    operations = [
        migrations.RunPython(fix_site_hostname, reverse_fix_site_hostname),
    ]
