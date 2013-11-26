from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from five import grok
from opengever.ogds.base.interfaces import IContactInformation
from opengever.ogds.base.utils import get_current_client
from opengever.ogds.base.utils import set_client_id
from plone.app.layout.viewlets import common
from zope.component import getUtility
from zope.interface import Interface


CLIENT_SELECTOR_CURRENT_CLIENT = 'current_client'

class ClientSelectorViewlet(common.ViewletBase):
    index = ViewPageTemplateFile('client_selector.pt')

    def get_current_client(self):
        # session = self.request.SESSION
        # current_client = session.get(CLIENT_SELECTOR_CURRENT_CLIENT)

        return get_current_client()

    def get_clients(self):
        info = getUtility(IContactInformation)
        return info.get_assigned_clients(userid='sk1m1')


class ChangeClientView(grok.View):
    grok.name('change_client')
    grok.context(Interface)

    def render(self):
        client_id = self.request.get('client_id')

        if client_id:
            set_client_id(client_id)

        return self.request.RESPONSE.redirect(self.context.absolute_url())
