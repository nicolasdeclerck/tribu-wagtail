# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Site vitrine de la compagnie de théâtre **La tribu d'Oya**, bâti sur **Django 6 / Wagtail 7.4** (Python 3.14). Tout le contenu est éditable depuis l'admin Wagtail. Le front utilise **Tailwind CSS v3** (compilé localement, sans Node), **Alpine.js** (interactivité) et **HTMX** (chargé, prêt pour des chargements partiels). La langue et les libellés d'admin sont en **français**.

## Commandes

```bash
source .venv/bin/activate

# CSS — nécessite d'abord ./bin/get-tailwind.sh (télécharge le binaire standalone dans tools/, non versionné)
./bin/build-css.sh            # build minifié one-off (theme/static_src/input.css → core/static/css/app.css)
./bin/build-css.sh --watch    # watcher dev, à lancer en parallèle du runserver

python manage.py migrate
python manage.py seed_content # idempotent : (ré)importe images/PDF et crée/met à jour toutes les pages
python manage.py runserver    # site sur :8000, admin sur /admin/

python manage.py test         # toute la suite
python manage.py test home.tests.HomeTests.test_homepage_is_renderable   # un seul test
```

`manage.py` pointe par défaut sur `tribu.settings.dev`. Les commandes ci-dessus utilisent donc automatiquement les settings de développement.

## Settings

`tribu/settings/` est un package à trois modules :
- `base.py` — config partagée (INSTALLED_APPS, Wagtail, i18n fr/Europe-Paris). SQLite par défaut.
- `dev.py` — `DEBUG=True`, SECRET_KEY en dur, `ALLOWED_HOSTS=["*"]`. Importe `.local` s'il existe (overrides non versionnés).
- `production.py` — `DEBUG=False`, secrets et base via variables d'environnement (`SECRET_KEY`, `DATABASE_URL`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`), `ManifestStaticFilesStorage`, durcissement HTTPS via `DJANGO_SECURE_SSL_REDIRECT`.

## Architecture

### Arbre de pages Wagtail

Chaque niveau est contraint par `parent_page_types` / `subpage_types` dans les modèles. Les pages index utilisent `max_count = 1`.

```
HomePage (/)                       home
├── CompagniePage (/compagnie/)    compagnie  → MembrePage enfants
│   └── MembrePage
├── ProjetIndexPage (/projets/)    projets    → ProjetPage enfants
│   └── ProjetPage                 + ProjetGalleryImage (Orderable inline)
├── StageIndexPage (/stages/)      stages     → StagePage enfants
│   └── StagePage                  + StageObjectif / StageAxeTravail / StageDate (Orderables inline)
└── ReseauxPage (/reseaux/)        reseaux
```

L'app `core` ne contient pas de modèle de page : elle regroupe les templates partagés (`base.html`, includes header/footer), les statiques (`core/static/`), les template tags, et la commande `seed_content`.

### Conventions de modèles

- Les enfants ordonnables (galeries, objectifs, dates…) sont des sous-classes de `wagtail.models.Orderable` reliées par `ParentalKey` avec un `related_name`, éditées via `InlinePanel`.
- Les pages index exposent leurs enfants au template en surchargeant `get_context()` avec un queryset `.child_of(self).live().order_by("ordre")` — le champ `ordre` (PositiveIntegerField) porte l'ordre d'affichage manuel.
- Images/documents sont des `ForeignKey` vers `wagtailimages.Image` / `wagtaildocs.Document` (`on_delete=SET_NULL`, `related_name="+"`).
- Le RichText de crédits restreint les fonctionnalités via la constante `CREDIT_FEATURES`.

### Approche « Wagtail-native » (important)

- **Navigation** : le header et le footer sont générés depuis l'arbre de pages, pas codés en dur. Le header s'appuie sur le champ natif `show_in_menus` / le queryset `.in_menu()`. Le footer utilise les template tags de `core/templatetags/tribu_tags.py` (`footer_projets`, `footer_stages`). Pour changer une entrée de menu : cocher « Afficher dans les menus » et glisser-déposer dans l'admin — aucun code à toucher.
- **SEO** : `base.html` consomme les champs natifs de l'onglet *Promotion* (`seo_title`, `search_description`, `slug`) pour title/meta/canonical/OpenGraph. Ne pas réimplémenter.
- **Recherche** : backend base de données Wagtail ; les modèles déclarent `search_fields`.

### Front / assets

- Tailwind reste en **v3** délibérément (préserve à l'identique les classes du site vanilla d'origine : `bg-opacity-*`, valeurs arbitraires `min-h-[80px]`, etc.). Globs de contenu dans `tailwind.config.js`.
- `core/static/js/app.js` enregistre deux composants Alpine : `homeCarousel` (accueil, autoplay 5 s) et `imageCarousel` (galerie projet). Le menu mobile est un `x-data="{ open: false }"` inline.

## Déploiement

Production via Docker Compose : **PostgreSQL 16** + **Gunicorn** (`web`) + **Nginx** (sert `/static` et `/media`, reverse-proxy). `docker/entrypoint.sh` enchaîne au boot : `migrate` → `collectstatic` → `seed_content` (si `SEED_CONTENT=1`) → superuser (si `DJANGO_SUPERUSER_*`) → Gunicorn. Le `Dockerfile` est multi-stage et compile le CSS via le binaire Tailwind Linux (adapté à `TARGETARCH`). Copier `.env.example` → `.env` avant `docker compose up -d --build`.

Le README (FR) détaille le démarrage rapide, le seed et le déploiement.
