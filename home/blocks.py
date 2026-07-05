"""
Blocs Wagtail de la « Section personnalisable » de la page d'accueil.

Ces blocs alimentent un StreamField (cf. `HomePage.custom_section`) : depuis
l'admin Wagtail, l'éditeur empile librement titres, textes riches, images,
boutons et la « Liste interactive » sous le carrousel. Chaque bloc a son propre
template dans `home/templates/home/blocks/`, stylé en **Tailwind** (pas de CSS
custom) et animé via **Alpine.js** (déjà chargé sur le site).
"""

from wagtail import blocks
from wagtail.images.blocks import ImageChooserBlock

CONTENT_FEATURES = ["bold", "italic", "ol", "ul", "link", "h3", "h4"]


class HeadingBlock(blocks.StructBlock):
    text = blocks.CharBlock(label="Texte du titre", max_length=255)

    class Meta:
        icon = "title"
        label = "Titre"
        template = "home/blocks/heading_block.html"


class ImageBlock(blocks.StructBlock):
    image = ImageChooserBlock(label="Image")
    caption = blocks.CharBlock(label="Légende", required=False, max_length=255)

    class Meta:
        icon = "image"
        label = "Image"
        template = "home/blocks/image_block.html"


class ButtonBlock(blocks.StructBlock):
    text = blocks.CharBlock(label="Libellé", max_length=80)
    link_page = blocks.PageChooserBlock(
        label="Lien vers une page",
        required=False,
        help_text="Page du site visée par le bouton (prioritaire sur le lien externe).",
    )
    url = blocks.URLBlock(
        label="Lien externe",
        required=False,
        help_text="Utilisé seulement si aucune page n'est choisie ci-dessus.",
    )
    size = blocks.ChoiceBlock(
        label="Taille du bouton",
        choices=[
            ("sm", "Petit"),
            ("base", "Normal"),
            ("lg", "Grand"),
            ("xl", "Très grand"),
        ],
        default="base",
    )

    class Meta:
        icon = "link"
        label = "Bouton / Lien"
        template = "home/blocks/button_block.html"


class SeparatorBlock(blocks.StructBlock):
    """Espace vide vertical pour aérer le contenu. Hauteur réglable en rem."""

    height = blocks.FloatBlock(
        label="Hauteur (rem)",
        default=2,
        min_value=0,
        help_text="Hauteur de l'espace vide, en rem (1 rem ≈ 16 px).",
    )

    class Meta:
        icon = "minus"
        label = "Séparateur (espace vide)"
        template = "home/blocks/separator_block.html"


class InteractiveListItemBlock(blocks.StructBlock):
    """Un item de la « Liste interactive » : titre, détail (sous-titre + texte)
    déplié sous le titre au survol, et image affichée dans le volet de droite."""

    title = blocks.CharBlock(label="Titre", max_length=120)
    subtitle = blocks.CharBlock(label="Sous-titre", required=False, max_length=200)
    content = blocks.RichTextBlock(
        label="Contenu détaillé", required=False, features=CONTENT_FEATURES
    )
    image = ImageChooserBlock(
        label="Image",
        required=False,
        help_text=(
            "Optionnel : s'affiche dans le volet de droite au survol de l'item "
            "(sous le titre sur mobile)."
        ),
    )
    link_page = blocks.PageChooserBlock(
        label="Lien vers une page",
        required=False,
        help_text="Optionnel : rend l'item cliquable vers cette page du site.",
    )

    class Meta:
        icon = "doc-full"
        label = "Item de la liste"


class InteractiveListBlock(blocks.StructBlock):
    """Liste interactive à deux volets.

    Sur desktop : la liste des titres s'affiche à gauche ; au survol (ou au
    focus clavier) d'un titre, son détail (sous-titre + texte riche) se déplie
    sous le titre tandis que son image apparaît à droite en fondu. Sur mobile,
    un appui sur le titre déplie tout le détail sous celui-ci (image puis
    textes). Le premier item est actif par défaut.
    """

    items = blocks.ListBlock(InteractiveListItemBlock(), label="Items", min_num=1)

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context=parent_context)
        # Le volet de droite (deux colonnes sur desktop) n'a de sens que si au
        # moins un item porte une image ; sinon on reste sur une seule colonne.
        context["has_image"] = any(item.get("image") for item in value["items"])
        return context

    class Meta:
        icon = "list-ul"
        label = "Liste interactive"
        template = "home/blocks/interactive_list_block.html"


class ParagraphBlock(blocks.StructBlock):
    """Bloc de texte riche avec une taille de police réglable (mappée sur les
    modificateurs `prose-*` du plugin typography, cf. template)."""

    text = blocks.RichTextBlock(label="Texte", features=CONTENT_FEATURES)
    size = blocks.ChoiceBlock(
        label="Taille du texte",
        choices=[
            ("sm", "Petit"),
            ("base", "Normal"),
            ("lg", "Grand"),
            ("xl", "Très grand"),
        ],
        default="base",
    )

    class Meta:
        icon = "pilcrow"
        label = "Texte riche"
        template = "home/blocks/paragraph_block.html"


class BaseContentBlock(blocks.StreamBlock):
    """Palette de blocs « simples », réutilisée telle quelle au niveau supérieur
    et dans chaque colonne du bloc « Colonnes ». Volontairement sans le bloc
    « Colonnes » lui-même pour interdire toute imbrication de colonnes."""

    heading = HeadingBlock()
    paragraph = ParagraphBlock()
    image = ImageBlock()
    button = ButtonBlock()
    interactive_list = InteractiveListBlock()
    separator = SeparatorBlock()

    class Meta:
        label = "Contenu"


class ColumnsBlock(blocks.StructBlock):
    """Bloc de structure : de 2 à 4 colonnes côte à côte sur desktop, empilées
    sur mobile. Chaque colonne contient librement les blocs de `BaseContentBlock`.

    Le nombre de colonnes = le nombre d'items ajoutés (borné à 2–4). La grille
    responsive est choisie dans le template selon `count` (classes en clair pour
    ne pas être purgées par Tailwind)."""

    columns = blocks.ListBlock(
        BaseContentBlock(),
        min_num=2,
        max_num=4,
        label="Colonnes",
        help_text="Ajoutez de 2 à 4 colonnes ; elles s'empilent sur mobile.",
    )

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context=parent_context)
        context["count"] = len(value["columns"])
        return context

    class Meta:
        icon = "grip"
        label = "Colonnes (2 à 4)"
        template = "home/blocks/columns_block.html"


class CustomSectionBlock(BaseContentBlock):
    """Palette proposée à l'admin dans la section personnalisable : tous les
    blocs de base plus le bloc de structure « Colonnes »."""

    columns = ColumnsBlock()

    class Meta:
        label = "Section personnalisable"
