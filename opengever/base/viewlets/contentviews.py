from opengever.base.interfaces import ICheckinCheckoutMenuItem
from plone.app.layout.viewlets.common import ContentViewsViewlet
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from zope.browsermenu.interfaces import IBrowserSubMenuItem
from zope.browsermenu.menu import getMenu
from zope.component import getAdapters
from zope.interface import Interface
from zope.interface import providedBy
from zope.interface.interfaces import IInterface
from zope.security.proxy import removeSecurityProxy


class ModelContentViewsViewlet(ContentViewsViewlet):
    """Provide correct edit links for a SQL-model based view.

    For plone content fall-back to default content views.
    """
    index = ViewPageTemplateFile('contentviews.pt')

    def prepareObjectTabs(self, default_tab='view', sort_first=('folderContents',)):
        """Prepare the object tabs by determining their order and working
        out which tab is selected. Used in global_contentviews.pt
        """

        if getattr(self.view, 'is_model_view', False):
            return self.prepare_model_tabs()
        else:
            tabs = super(ModelContentViewsViewlet, self).prepareObjectTabs(
                default_tab, sort_first)
            if getattr(self.view, 'is_model_proxy_view', False):
                tabs = self.view.prepare_model_proxy_tabs(tabs)
            return tabs

    def prepare_model_tabs(self):
        model = self.view.model
        return ({
            'category': 'object',
            'available': True,
            'description': u'',
            'icon': '',
            'title': u'Edit',
            'url': model.get_edit_url(self.view.context),
            'selected': self.view.is_model_edit_view,
            'visible': True,
            'allowed': True,
            'link_target': None,
            'id': 'edit'
        },)

    def menu(self):
        result = []
        for name, item in getAdapters((self.context, self.request), ICheckinCheckoutMenuItem):
            if item.available():
                result.append(item)

        # Now order the result. This is not as easy as it seems.
        #
        # (1) Look at the interfaces and put the more specific menu entries
        #     to the front.
        # (2) Sort unambigious entries by order and then by title.
        ifaces = list(providedBy(removeSecurityProxy(self.context)).__iro__)
        max_key = len(ifaces)
        def iface_index(item):
            iface = item._for
            if not iface:
                iface = Interface
            if IInterface.providedBy(iface):
                return ifaces.index(iface)
            if isinstance(removeSecurityProxy(self.context), item._for):
                # directly specified for class, this goes first.
                return -1
            # no idea. This goes last.
            return max_key
        result = [(iface_index(item), item.order, item.title, item)
                  for item in result]
        result.sort()

        result = [
            {'title': title,
             'description': item.description,
             'action': item.action,
             'selected': (item.selected() and u'selected') or u'',
             'icon': item.icon,
             'extra': item.extra,
             'submenu': (IBrowserSubMenuItem.providedBy(item) and
                         getMenu(item.submenuId, self.context, self.request)) or None}
            for index, order, title, item in result]

        return result
