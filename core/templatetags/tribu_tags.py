from django import template

register = template.Library()


@register.simple_tag
def footer_projets():
    """Published projets (excluding works-in-progress) for the footer."""
    from projets.models import ProjetPage

    return (
        ProjetPage.objects.live()
        .filter(is_in_progress=False)
        .order_by("ordre")
    )


@register.simple_tag
def contact_page():
    """The (unique) published contact page, or None."""
    from contact.models import FormPage

    return FormPage.objects.live().first()


@register.simple_tag
def footer_stages():
    """Published stages for the footer."""
    from stages.models import StagePage

    return StagePage.objects.live().order_by("ordre")
