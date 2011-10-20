from Products.CMFCore.interfaces._tools import IMemberData
from Products.PluggableAuthService.interfaces.authservice import \
    IPropertiedUser
from StringIO import StringIO
from five import grok
from opengever.ogds.base.interfaces import IContactInformation
from xlwt import Workbook, XFStyle
from zope.component import getUtility
from zope.interface import Interface
from zope.i18n import translate


class ReportingController(grok.View):
    """The controllerview check if the actual user has the permissions to acces
    the inbox.
    """

    grok.context(Interface)
    grok.name('reporting_controller')

    def render(self):
        """check if the user is in the inbox group."""

        info = getUtility(IContactInformation)
        return info.is_user_in_inbox_group()


def format_datetime(date):
    """helper method for formatting a dattime in to string"""
    if date:
        return date.strftime('%d.%m.%Y %H:%M')
    return None


def readable_author(author):
    """Helper method which returns the author description,
    instead of the userid"""

    if not isinstance(author, unicode):
        if author is not None:
            author = author.decode('utf-8')
        else:
            return author
    if IPropertiedUser.providedBy(author) or IMemberData.providedBy(author):
        author = author.getId()
    info = getUtility(IContactInformation)
    if info.is_user(author) or info.is_contact(author) \
                                or info.is_inbox(author):
        return info.describe(author)
    else:
        return author


class StringTranslater(object):
    """provide the translate method as helper method
    for the given domain and request"""

    def __init__(self, request, domain):
        self.request = request
        self.domain = domain

    def translate(self, value):
        """ return the translated string"""

        if value:
            return translate(value, domain=self.domain, context=self.request)
        return None


def get_date_style(format='D.M.YY h:mm'):
    """ Set up a date format style to use in the spreadsheet and return it."""
    excel_date_fmt = format
    style = XFStyle()
    style.num_format_str = excel_date_fmt
    return style


class XLSReporter(object):
    """XLS Reporter View generates a xls-report for the given results set.
    """

    def __init__(self, request, attributes, results):
        """Initalize the XLS reporter
        Arguments:
        attributes -- a list of mappings (with 'id', 'title', 'transform')
        results -- a list of objects, brains or sqlalchemy objects
        """

        self.attributes = attributes
        self.results = results
        self.request = request

    def __call__(self):
        """Generates the xls data for the given objects.
        """

        w = Workbook()
        sheet = w.add_sheet('Dossiers')

        #create labels row
        for i, attr in enumerate(self.attributes):
            sheet.write(0, i,
                translate(attr.get('title', ''), context=self.request))

        for r, dossier in enumerate(self.results):
            for c, attr in enumerate(self.attributes):

                value = getattr(dossier, attr.get('id'))

                # transform the value when a transform is given
                if attr.get('transform'):
                    value = attr.get('transform')(value)

                # set a XFStyle, when one is given
                if attr.get('style'):
                    sheet.write(r + 1, c, value, attr.get('style'))
                else:
                    sheet.write(r + 1, c, value)

        # save the Workbook-data in to a StringIO
        data = StringIO()
        w.save(data)
        data.seek(0)
        return data.read()