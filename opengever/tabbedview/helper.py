from ftw.mail.utils import get_header
from opengever.base import _ as base_mf
from opengever.base.browser.helper import get_css_class
from opengever.document.browser.download import DownloadConfirmationHelper
from opengever.document.document import Document
from opengever.mail.mail import OGMail
from opengever.ogds.base.actor import Actor
from opengever.ogds.base.utils import ogds_service
from plone.i18n.normalizer.interfaces import IIDNormalizer
from plone.memoize import ram
from Products.CMFCore.interfaces._tools import IMemberData
from Products.CMFPlone import PloneMessageFactory as pmf
from Products.PluggableAuthService.interfaces.authservice import IPropertiedUser
from zope.app.component.hooks import getSite
from zope.component import getMultiAdapter
from zope.component import getUtility
from zope.globalrequest import getRequest
from zope.i18n import translate
import cgi
import pkg_resources


try:
    pkg_resources.get_distribution('opengever.pdfconverter')
except pkg_resources.DistributionNotFound:
    PDFCONVERTER_AVAILABLE = False
else:
    PDFCONVERTER_AVAILABLE = True


def org_unit_title_helper(item, value):
    return item.get_issuing_org_unit().label()


def display_org_unit_title_condition():
    """A helper for hiding the org-unit title from a task listing if we
    have a single org-unit setup (it would be the same all the time).
    """
    return ogds_service().has_multiple_org_units()


def task_id_checkbox_helper(item, value):
    """ Checkbox helper based on tasks id attribute
    """

    attrs = {
        'type': 'checkbox',
        'class': 'noborder selectable',
        'name': 'task_ids:list',
        'id': item.task_id,
        'value': item.task_id,
        'title': 'Select %s' % item.title,
        }

    return '<input %s />' % ' '.join(['%s="%s"' % (k, v)
                                      for k, v in sorted(attrs.items())])


def author_cache_key(m, i, author):
    if IPropertiedUser.providedBy(author) or IMemberData.providedBy(author):
        return author.getId()
    else:
        return author


@ram.cache(author_cache_key)
def readable_ogds_author(item, author):
    if getattr(item, 'portal_type', None) == 'ftw.mail.mail':
        if getattr(item, 'msg', None):
            # Object
            author = get_header(item.msg, 'From')
        else:
            # Brain
            author = item.document_author

    if not isinstance(author, unicode):
        if author is not None:
            author = author.decode('utf-8')
        else:
            author = ''

    return Actor.lookup(author).get_label()


@ram.cache(author_cache_key)
def readable_ogds_user(item, userid):
    if not isinstance(userid, unicode):
        if userid is not None:
            userid = userid.decode('utf-8')
        else:
            userid = ''

    return Actor.user(userid).get_label()


@ram.cache(author_cache_key)
def linked_ogds_author(item, author):
    return Actor.lookup(author).get_link()


def _breadcrumbs_from_item(item):
    """Returns a list of titles for the items parent hierarchy (breadcrumbs).
    `item` can be either a brain or an object.
    """
    breadcrumb_titles = []
    raw_breadcrumb_titles = getattr(item, 'breadcrumb_titles', None)
    if not raw_breadcrumb_titles:
        # Not a brain - get breadcrumbs from the breadcrumbs view
        breadcrumbs_view = getMultiAdapter((item, item.REQUEST),
                                           name='breadcrumbs_view')
        raw_breadcrumb_titles = breadcrumbs_view.breadcrumbs()

    # Make sure all titles are utf-8
    for elem in raw_breadcrumb_titles:
        title = elem.get('Title')
        if isinstance(title, unicode):
            title = title.encode('utf-8')
        breadcrumb_titles.append(title)

    return breadcrumb_titles


def linked(item, value):
    """Takes an item (object or brain) and returns a HTML snippet that
    contains a link to the item, it's icon and breadcrumbs in the tooltip.
    """

    if isinstance(value, unicode):
        value = value.encode('utf-8')

    # Determine URL method
    url_method = lambda: '#'
    if hasattr(item, 'getURL'):
        url_method = item.getURL
    elif hasattr(item, 'absolute_url'):
        url_method = item.absolute_url

    # Construct CSS class
    css_class = get_css_class(item)

    # Construct breadcrumbs
    breadcrumb_titles = _breadcrumbs_from_item(item)
    link_title = " > ".join(t for t in breadcrumb_titles)

    # Make sure all data used in the HTML snippet is properly escaped
    link_title = cgi.escape(link_title, quote=True)
    value = cgi.escape(value, quote=True)

    link = '<a class="rollover-breadcrumb %s" href="%s" title="%s">%s</a>' % (
        css_class, url_method(), link_title, value)

    wrapper = '<span class="linkWrapper">%s</span>' % link
    return wrapper


def linked_document_with_tooltip(item, value):
    """Wrapper method for the _linked_document_with_tooltip method
    for normal not trashed documents and mails."""

    return _linked_document_with_tooltip(item, value)


def linked_trashed_document_with_tooltip(item, value):
    """Wrapper method for the _linked_document_with_tooltip method
    for normal but trashed documents and mails."""

    if item.review_state in [Document.removed_state, OGMail.removed_state]:
        removed = True
    else:
        removed = False

    return _linked_document_with_tooltip(item, value, trashed=True,
                                         removed=removed)


def _linked_document_with_tooltip(item, value, trashed=False, removed=False):
    data = {}

    if isinstance(value, unicode):
        value = value.encode('utf-8')
    data['value'] = value

    # Determine URL method
    data['url'] = '#'
    if hasattr(item, 'getURL'):
        data['url'] = item.getURL()
    elif hasattr(item, 'absolute_url'):
        data['url'] = item.absolute_url()

    # tooltip links
    data['preview_link'] = '%s/@@download_pdfpreview' % (data['url'])
    data['preview_label'] = translate(
        base_mf(u'button_pdf', 'PDF'), context=item.REQUEST).encode('utf-8')

    data['edit_metadata_link'] = '%s/edit_checker' % (data['url'])
    data['edit_metadata_label'] = translate(
        pmf(u'Edit metadata'), context=item.REQUEST).encode('utf-8')

    data['edit_direct_link'] = '%s/editing_document' % (data['url'])
    data['edit_direct_label'] = translate(
        pmf(u'Checkout and edit'), context=item.REQUEST).encode('utf-8')

    # Construct CSS class
    data['css_class'] = get_css_class(item)

    # Construct breadcrumbs
    breadcrumb_titles = _breadcrumbs_from_item(item)
    data['breadcrumbs'] = " > ".join(t for t in breadcrumb_titles)

    # Make sure all data used in the HTML snippet is properly escaped
    for k, v in data.items():
        data[k] = cgi.escape(v, quote=True)

    tooltip_links = []

    is_doc = item.portal_type == 'opengever.document.document'

    if is_doc and PDFCONVERTER_AVAILABLE:
        tooltip_links.append("""<a href='%(preview_link)s'>
                    %(preview_label)s
                </a>""" % data)

    if not trashed:
        tooltip_links.append("""<a href='%(edit_metadata_link)s'>
                    %(edit_metadata_label)s
                </a>""" % data)

    if is_doc and not trashed:
        tooltip_links.append("""<a href='%(edit_direct_link)s'>
                    %(edit_direct_label)s
                </a>""" % data)

    if is_doc:
        dc_helper = DownloadConfirmationHelper()
        tooltip_links.append(
            dc_helper.get_html_tag(data['url']))

    if removed:
        data['removed_span'] = "<span class='removed_document'></span>"
    else:
        data['removed_span'] = ''

    data['tooltip_links'] = """
                """.join(tooltip_links)

    link = """
    <div class='linkWrapper'>
        %(removed_span)s
        <a class='tabbedview-tooltip %(css_class)s' href='%(url)s'></a>
        <a href='%(url)s'>%(value)s</a>
        <div class='tabbedview-tooltip-data'>
            <div class='tooltip-content'>
                <div class='tooltip-header'>%(value)s</div>
                <div class='tooltip-breadcrumb'>%(breadcrumbs)s</div>
                <div class='tooltip-links'>
                    %(tooltip_links)s
                </div>
            </div>
            <div class='bottomImage'></div>
        </div>
    </div>""" % data

    return link


def readable_date_set_invisibles(item, date):
    if not date or str(date) == '1970/01/01' \
            or str(date) == '1970-01-01 00:00:00':
        return u''
    strftimestring = '%d.%m.%Y'

    if date is None:
        return None
    return date.strftime(strftimestring)


def email_helper(item, value):
    if value:
        return '<a href="mailto:%s">%s</a>' % (value, value)
    else:
        return ''


def boolean_helper(item, value):
    """Helper for displaying a boolean field in human readable form.
    """

    request = getRequest()
    if value:
        return translate('Yes', domain='plone', context=request)

    return translate('No', domain='plone', context=request)


def workflow_state(item, value):
    """Helper which translates the workflow_state in plone domain
    and adds a CSS class to indicate the worflow state.
    """

    normalize = getUtility(IIDNormalizer).normalize
    state = normalize(item.review_state)
    # We use zope.globalrequest because item can be a SQLAlchemy `Task` object
    # which doesn't have a request
    request = getRequest()
    return """<span class="wf-%s">%s</span>""" % (
        state, translate(value, domain='plone', context=request))


def queue_view_helper(item, value):
    site = getSite()
    return """<a href='%s/jobs_view?queue=%s'>%s</a>""" % (
        site.absolute_url(), value, value)


def external_edit_link(item, value):
    """Return a link Tag to the checkout_documents view,
    with the external_edit mode selected """
    if item.portal_type != 'opengever.document.document':
        return ''
    #item = hasattr(item, 'aq_explicit') and item.aq_explicit or item
    if hasattr(item, 'getURL'):
        url = item.getURL()
    elif hasattr(item, 'absolute_url'):
        url = item.absolute_url()
    else:
        return ''

    url = '%s/editing_document' % url

    return '<a id="%s" title="%s" href="%s" class="function-edit"></a>' % (
        item.id,
        getSite().translate(
            'checkout_and_edit', domain="opengever.tabbedview"),
        url)


def translated_string(domain='plone'):
    domain = domain

    def _translate(item, value):
        return translate(
            value, context=getRequest(), domain=domain)
    return _translate
