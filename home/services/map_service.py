from home.models import Parish
from django.utils.translation import gettext as _


def get_latitude_longitude(point):
    return [point.coords[1], point.coords[0]]


def get_popup_and_color(parish: Parish, church):
    if parish.one_page_has_confessions():
        wording = _("ConfessionsExist")
        color = 'blue'
    elif not parish.has_pages() or not parish.all_pages_scraped():
        wording = _("NotScrapedYet")
        color = 'beige'
    elif not parish.one_page_has_confessions():
        wording = _("NoConfessionFound")
        color = 'black'
    else:
        raise NotImplemented

    link_wording = _("JumpBelow")
    popup_html = f"""
        <b>{church.name}</b><br>
        {wording}<br>
        <a href="#{parish.uuid}" target="_parent">{link_wording}</a>
    """

    return popup_html, color


