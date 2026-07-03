# La tribu d'Oya — site Wagtail

Migration technique du site vitrine de la compagnie **La tribu d'Oya**, du vanilla
(HTML/JS/Tailwind via CDN) vers **Django + Wagtail**. Le rendu, le style et les
fonctionnalités sont identiques ; le contenu est désormais éditable depuis l'admin
Wagtail.

## Stack

- **Django 6 / Wagtail 7.4** (Python 3.14)
- **Tailwind CSS v3** compilé localement (CLI standalone, sans Node)
- **Alpine.js** pour l'interactivité front (menu mobile, carousels)
- **HTMX** disponible pour d'éventuels chargements partiels côté serveur
- Base **SQLite** par défaut (dev)

## Démarrage rapide

```bash
cd tribu-wagtail
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 1. Outil Tailwind (binaire standalone, ~48 Mo, non versionné)
./bin/get-tailwind.sh
./bin/build-css.sh

# 2. Base de données + contenu
python manage.py migrate
python manage.py seed_content        # importe images, documents et pages
python manage.py createsuperuser

# 3. Lancer
python manage.py runserver
```

- Site : http://127.0.0.1:8000/
- Admin Wagtail : http://127.0.0.1:8000/admin/

Pendant le développement front, lancer le watcher Tailwind en parallèle :

```bash
./bin/build-css.sh --watch
```

## Architecture

Arbre de pages Wagtail (tout est éditable dans l'admin) :

```
HomePage  (/)                      → carousel plein écran (stages + projets)
├── CompagniePage (/compagnie/)    → présentation + grille équipe
│   └── MembrePage (/compagnie/<slug>/)
├── ProjetIndexPage (/projets/)
│   └── ProjetPage (/projets/<slug>/)      + galerie d'images (orderable)
├── StageIndexPage (/stages/)
│   └── StagePage (/stages/<slug>/)        + objectifs / axes / dates (orderables)
└── ReseauxPage (/reseaux/)
```

| App         | Modèles                                                        |
|-------------|----------------------------------------------------------------|
| `home`      | `HomePage`                                                     |
| `compagnie` | `CompagniePage`, `MembrePage`                                  |
| `projets`   | `ProjetIndexPage`, `ProjetPage`, `ProjetGalleryImage`         |
| `stages`    | `StageIndexPage`, `StagePage`, `StageObjectif`, `StageAxeTravail`, `StageDate` |
| `reseaux`   | `ReseauxPage`                                                  |
| `core`      | templates partagés (`base.html`, header/footer), statiques, tags, commande `seed_content` |

### Approche « Wagtail-native »

- **Navigation** : générée depuis l'arbre de pages via le champ natif
  `show_in_menus` et le queryset `.in_menu()` (header & footer). Pour ajouter /
  retirer / réordonner une entrée de menu, il suffit de cocher *Afficher dans les
  menus* et de glisser-déposer la page dans l'admin — aucun code à toucher.
- **SEO** : champs natifs de l'onglet *Promotion* (`seo_title`, `search_description`,
  `slug`). `base.html` se contente de les consommer (title, meta description,
  canonical, Open Graph / Twitter).
- **Médias** : images et PDF gérés par la bibliothèque Wagtail (`wagtailimages`,
  `wagtaildocs`) avec renditions automatiques.

## Style (Tailwind)

- Source : `theme/static_src/input.css`
- Config / globs de contenu : `tailwind.config.js`
- Sortie : `core/static/css/app.css` (chargée par `base.html`)

On reste en **Tailwind v3** pour conserver à l'identique les classes du site
original (`bg-opacity-*`, valeurs arbitraires `min-h-[80px]`, etc.).

## Interactivité (Alpine / HTMX)

`core/static/js/app.js` enregistre deux composants Alpine :

- `homeCarousel` — carousel plein écran de l'accueil (autoplay 5 s, flèches,
  clavier ; tout contrôle manuel coupe l'autoplay — comportement repris de Glide.js).
- `imageCarousel` — galerie d'images des pages projet.

Le menu mobile est un simple `x-data="{ open: false }"`. HTMX est chargé et prêt
à l'emploi pour des chargements partiels si le besoin apparaît.

## Contenu

`python manage.py seed_content` est **idempotent** : il (ré)importe les images de
`core/static/img`, les PDF de `core/static/documents`, et crée/met à jour toutes
les pages avec le contenu d'origine. À lancer une fois après `migrate`, puis gérer
le contenu depuis l'admin.

## Déploiement (Docker Compose)

Stack de production : **PostgreSQL** + **Gunicorn** (app) + **Nginx** (sert
`/static` et `/media`, reverse-proxy vers Gunicorn).

```bash
cp .env.example .env
# Éditer .env : SECRET_KEY (obligatoire), ALLOWED_HOSTS, CSRF_TRUSTED_ORIGINS,
# POSTGRES_PASSWORD + DATABASE_URL cohérents, etc.

docker compose up -d --build
```

Au premier démarrage, le conteneur `web` (via `docker/entrypoint.sh`) exécute
automatiquement : `migrate` → `collectstatic` → `seed_content` (si `SEED_CONTENT=1`)
→ création du superuser (si `DJANGO_SUPERUSER_*` est défini), puis lance Gunicorn.

- Site : http://localhost (ou `NGINX_PORT`)
- Admin : http://localhost/admin/

### Services

| Service | Rôle                                                         |
|---------|--------------------------------------------------------------|
| `db`    | PostgreSQL 16, données dans le volume `pgdata`               |
| `web`   | Image applicative (Gunicorn). Volumes partagés `static`, `media` |
| `nginx` | Sert `/static` + `/media` (volumes) et proxifie le reste vers `web` |

### Composants de déploiement

- `Dockerfile` — build multi-stage : (1) compile Tailwind via le binaire standalone
  Linux (adapté à l'architecture via `TARGETARCH`), (2) construit le venv Python,
  (3) image runtime minimale.
- `docker-compose.yml` — orchestration des 3 services + volumes.
- `docker/entrypoint.sh` — migrations, static, seed/superuser optionnels, démarrage.
- `docker/nginx/default.conf` — config Nginx (static/media + proxy).
- `.env.example` — toutes les variables (copier en `.env`, jamais versionné).
- `tribu/settings/production.py` — `DEBUG=False`, secrets et base via l'environnement
  (`SECRET_KEY`, `DATABASE_URL`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`),
  `ManifestStaticFilesStorage`, durcissement HTTPS activable via
  `DJANGO_SECURE_SSL_REDIRECT=true`.

### TLS / HTTPS

Le `default.conf` écoute en HTTP (port 80). En production, placer un terminateur
TLS devant Nginx (Traefik, Caddy, certbot, ou le load-balancer de l'hébergeur),
puis passer `DJANGO_SECURE_SSL_REDIRECT=true` dans `.env`. Le header
`X-Forwarded-Proto` est déjà pris en compte côté Django.

### Mises à jour

```bash
git pull
docker compose up -d --build   # rebuild (recompile le CSS) + migrations auto au boot
```
# tribu-wagtail
