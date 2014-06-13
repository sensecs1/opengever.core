from five import grok
from opengever.base.browser.helper import get_css_class
from opengever.dossier.browser.overview import DossierOverview
from opengever.globalindex.interfaces import ITaskQuery
from opengever.globalindex.model.task import Task
from opengever.inbox import _
from opengever.inbox.browser.tabs import get_current_inbox_principal
from opengever.inbox.inbox import IInbox
from opengever.ogds.base.utils import get_current_admin_unit
from opengever.ogds.base.utils import get_current_org_unit
from opengever.task import OPEN_TASK_STATES
from Products.CMFCore.utils import getToolByName
from sqlalchemy import and_
from sqlalchemy import desc
from sqlalchemy import or_
from zope.component import getUtility


class InboxOverview(DossierOverview):
    """Displayes the Inbox Overview
    """
    grok.context(IInbox)
    grok.name('tabbedview_view-overview')

    def boxes(self):
        """Defines the boxes wich are Displayed at the Overview tab"""

        items = [[dict(id='assigned_inbox_tasks',
                       content=self.assigned_tasks(),
                       label=_(u'label_assigned_inbox_tasks',
                               default='Assigned tasks')),
                  dict(id='issued_inbox_tasks',
                       content=self.issued_tasks(),
                       label=_(u'label_issued_inbox_tasks',
                               default='Issued tasks')), ],
                 [dict(id='documents',
                       content=self.documents()), ]]
        return items

    def assigned_tasks(self):
        """Returns the 5 last modified open task which are assigned
        to the current org unit's inbox.
        """
        current_inbox_id = get_current_org_unit().inbox().id()
        query = Task.query.users_tasks(current_inbox_id)
        query = query.filter(Task.review_state.in_(OPEN_TASK_STATES))
        query = query.order_by(desc(Task.modified))

        return query.limit(5).all()

    def issued_tasks(self):
        """Returns the 5 last modified open task which are issued
        by the current org unit's inbox.
        """
        current_inbox_id = get_current_org_unit().inbox().id()
        query = Task.query.users_issued_tasks(current_inbox_id)
        query = query.filter(Task.review_state.in_(OPEN_TASK_STATES))
        query = query.order_by(desc(Task.modified))

        return query.limit(5).all()

    def documents(self):
        """
        Get documents and mails that are directly contained in
        the inbox, but not in forwardings.

        It only queries documents from the current_org_unit
        (all inbox documents are marked with the containing org_unit
        in the `client_id` metadata).
        """

        catalog = self.context.portal_catalog
        query = {'isWorkingCopy': 0,
                 'path': {'depth': 1,
                          'query': '/'.join(self.context.getPhysicalPath())},
                 'portal_type': ['opengever.document.document',
                                 'ftw.mail.mail'],
                 'client_id': get_current_org_unit().id()}
        documents = catalog(query)[:10]

        document_list = [{
            'Title': document.Title,
            'getURL': document.getURL,
            'alt': document.document_date and
            document.document_date.strftime('%d.%m.%Y') or '',
            'css_class': get_css_class(document),
            'portal_type': document.portal_type,
        } for document in documents]

        return document_list
