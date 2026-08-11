"""Générateurs de données structurées JSON-LD schema.org (TheaterEvent,
PerformingGroup, BreadcrumbList) pour les pages spectacle et l'accueil.

Même convention que ProPage._structured_data (pros/models.py) : chaque dict
porte son propre "@context" et dumps_json_ld() échappe « </ » pour ne pas
pouvoir fermer prématurément la balise <script>.
"""
import json
import re
from datetime import time

from django.utils.html import strip_tags
from django.utils.text import Truncator

_RE_HORAIRE_H = re.compile(r"(\d{1,2})\s*h(?:\.?\s*(\d{2}))?")
_RE_HORAIRE_COLON = re.compile(r"(\d{1,2}):(\d{2})")

_RE_CODE_POSTAL = re.compile(r"(\d{5})\s+([A-Za-zÀ-ÿ'\-\. ]+?)\s*$")
_RE_DEBUT_ADRESSE = re.compile(
    r"\d+(?:\s?(?:bis|ter|quater))?\s+"
    r"(?:rue|bd|boulevard|avenue|av\.|place|pl\.|chemin|allée|allee|impasse|quai)\b",
    re.IGNORECASE,
)


def parse_horaire(horaire):
    """Extrait l'heure de début d'un horaire en texte libre (ex. « 20h30 »,
    « 20:30 »). Retourne None si l'horaire est vide ou non reconnu."""
    if not horaire:
        return None
    match = _RE_HORAIRE_H.search(horaire) or _RE_HORAIRE_COLON.search(horaire)
    if not match:
        return None
    heure = int(match.group(1))
    minute = int(match.group(2)) if match.group(2) else 0
    if heure > 23 or minute > 59:
        return None
    return time(heure, minute)


def _place_dict(lieu):
    """Découpe un lieu en texte libre (souvent « nom - adresse, CP ville »)
    en Place/PostalAddress schema.org."""
    match_cp = _RE_CODE_POSTAL.search(lieu)
    if not match_cp:
        address = {"@type": "PostalAddress", "addressCountry": "FR"}
        if "lille" in lieu.lower():
            address["addressLocality"] = "Lille"
        return {"@type": "Place", "name": lieu, "address": address}

    code_postal, ville = match_cp.group(1), match_cp.group(2)
    avant_cp = lieu[: match_cp.start()]
    address = {
        "@type": "PostalAddress",
        "postalCode": code_postal,
        "addressLocality": ville,
        "addressCountry": "FR",
    }

    match_rue = _RE_DEBUT_ADRESSE.search(avant_cp)
    if not match_rue:
        return {"@type": "Place", "name": lieu, "address": address}

    nom = avant_cp[: match_rue.start()].strip(" ,-—–")
    rue = avant_cp[match_rue.start():].strip(" ,-—–")
    address["streetAddress"] = rue
    return {"@type": "Place", "name": nom, "address": address}


def theater_event_dict(request, representation):
    """JSON-LD TheaterEvent pour une représentation à venir et datée."""
    page = representation.page
    lieu = (representation.lieu or "").strip()
    nom = f"{page.title} — {lieu}" if lieu else page.title

    heure = parse_horaire(representation.horaire)
    if heure is not None:
        start_date = f"{representation.date.isoformat()}T{heure.strftime('%H:%M')}:00"
    else:
        start_date = representation.date.isoformat()

    data = {
        "@context": "https://schema.org",
        "@type": "TheaterEvent",
        "name": nom,
        "startDate": start_date,
        "eventStatus": "https://schema.org/EventScheduled",
        "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
        "url": request.build_absolute_uri(page.url),
    }
    if page.background_image:
        rendition = page.background_image.get_rendition("width-1200")
        data["image"] = request.build_absolute_uri(rendition.url)
    if lieu:
        data["location"] = _place_dict(lieu)
    if representation.billetterie:
        data["offers"] = {
            "@type": "Offer",
            "url": representation.billetterie,
            "availability": "https://schema.org/InStock",
        }
    return data


def organization_dict(request, description=""):
    """JSON-LD PerformingGroup pour la compagnie, affiché sur l'accueil."""
    return {
        "@context": "https://schema.org",
        "@type": "PerformingGroup",
        "name": "La tribu d'Oya",
        "url": request.build_absolute_uri("/"),
        "description": Truncator(strip_tags(description or "")).chars(300),
    }


def breadcrumbs_dict(request, page):
    """JSON-LD BreadcrumbList depuis l'arbre de pages Wagtail."""
    ancetres = list(page.get_ancestors().filter(depth__gt=1)) + [page]
    items = [
        {
            "@type": "ListItem",
            "position": position,
            "name": ancetre.title,
            "item": request.build_absolute_uri(ancetre.url),
        }
        for position, ancetre in enumerate(ancetres, start=1)
    ]
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": items,
    }


def dumps_json_ld(donnees):
    """Sérialise une liste d'objets JSON-LD pour injection dans un <script>."""
    return json.dumps(donnees, ensure_ascii=False).replace("</", "<\\/")
