from five import grok
from ftw.dictstorage.interfaces import ISQLAlchemy
from ftw.tabbedview.browser.listing import CatalogListingView
from ftw.tabbedview.interfaces import ITabbedView
from ftw.table import helper
from opengever.base.browser.helper import client_title_helper
from opengever.ogds.base.interfaces import IContactInformation
from opengever.tabbedview import _
from opengever.tabbedview.helper import readable_date_set_invisibles
from opengever.tabbedview.helper import readable_ogds_author, linked
from opengever.tabbedview.helper import workflow_state

from opengever.task.helper import task_type_helper
from zope.app.pagetemplate import ViewPageTemplateFile
from zope.component import getUtility
from zope.interface import implements
import re


class OpengeverTab(object):
    implements(ISQLAlchemy)

    show_searchform = True

    template = ViewPageTemplateFile('generic.pt')

    def get_css_classes(self):
        if self.show_searchform:
            return ['searchform-visible']
        else:
            return ['searchform-hidden']

    # XXX : will be moved to registry later...
    extjs_enabled = True

    def custom_sort(self, results, sort_on, sort_reverse):
        """We need to handle some sorting for special columns, which are
        not sortable in the catalog...
        """

        if getattr(self, '_custom_sort_method', None) is not None:
            results = self._custom_sort_method(results, sort_on, sort_reverse)

        elif sort_on=='reference':
            splitter = re.compile('[/\., ]')

            def _sortable_data(brain):
                """ Converts the "reference" into a tuple containing integers,
                which are converted well. Sorting "10" and "2" as strings
                results in wrong order..
                """

                value = getattr(brain, sort_on, '')
                if not isinstance(value, str) and not isinstance(
                    value, unicode):
                    return value
                parts = []
                for part in splitter.split(value):
                    part = part.strip()
                    try:
                        part = int(part)
                    except ValueError:
                        pass
                    parts.append(part)
                return parts
            results = list(results)
            results.sort(
                lambda a, b: cmp(_sortable_data(a), _sortable_data(b)))
            if sort_reverse:
                results.reverse()

        elif sort_on in ('responsible',
                         'Creator', 'checked_out', 'issuer', 'contact'):
            info = getUtility(IContactInformation)

            def _sorter(a, b):
                av = (info.describe(getattr(a, sort_on, '')) or '').lower()
                bv = (info.describe(getattr(b, sort_on, '')) or '').lower()
                return cmp(av, bv)

            results = list(results)
            results.sort(_sorter)
            if sort_reverse:
                results.reverse()
        return results


class OpengeverCatalogListingTab(grok.CodeView, OpengeverTab,
                                 CatalogListingView):
    """Base view for catalog listing tabs.
    """

    grok.context(ITabbedView)

    columns = ()

    search_index = 'SearchableText'
    sort_on = 'modified'
    sort_order = 'reverse'

    __call__ = CatalogListingView.__call__
    update = CatalogListingView.update
    render = __call__



class Documents(OpengeverCatalogListingTab):
    """List all documents recursively. Working copies are not listed.
    """

    grok.name('tabbedview_view-documents')

    types = ['opengever.document.document', 'ftw.mail.mail']

    search_options = {'isWorkingCopy': 0,}

    columns = (
        ('', helper.draggable),
        ('', helper.path_checkbox),

        {'column': 'Title',
         'column_title': _(u'label_title', default=u'Title'),
         'sort_index' : 'sortable_title',
         'transform': linked},

        {'column':'document_author',
         'column_title':_('label_document_author', default="Document Author"),
         'transform': readable_ogds_author},

        {'column':'document_date',
         'column_title':_('label_document_date', default="Document Date"),
         'transform':helper.readable_date},

        {'column':'receipt_date',
         'column_title':_('label_receipt_date', default="Receipt Date"),
         'transform':helper.readable_date},

        {'column':'delivery_date',
         'column_title':_('label_delivery_date', default="Delivery Date"),
         'transform':helper.readable_date},

        {'column':'checked_out',
         'column_title':_('label_checked_out', default="Checked out by"),
         'transform':readable_ogds_author},

        {'column':'containing_subdossier',
         'column_title':_('label_subdossier', default="Subdossier"),},
        )

    enabled_actions = ['cut',
                       'copy',
                       'send_as_email',
                       'checkout',
                       'checkin',
                       'cancel',
                       'create_task',
                       'trashed',
                       'send_documents',
                       'copy_documents_to_remote_client',
                       'move_items',
                       ]

    major_actions = ['send_documents',
                     'checkout',
                     'checkin',
                     'create_task',
                     ]


class Dossiers(OpengeverCatalogListingTab):

    grok.name('tabbedview_view-dossiers')

    object_provides = 'opengever.dossier.behaviors.dossier.IDossierMarker'

    columns = (
        ('', helper.draggable),
        ('', helper.path_checkbox),

        {'column': 'reference',
         'column_title': _(u'label_reference', default=u'Reference Number')},

        {'column': 'Title',
         'column_title': _(u'label_title', default=u'Title'),
         'sort_index' : 'sortable_title',
         'transform': linked},

        {'column': 'review_state',
         'column_title': _(u'label_review_state', default=u'Review state'),
         'transform': workflow_state},

        {'column':'responsible',
         'column_title':_(u'label_dossier_responsible',
                          default=u"Responsible"),
         'transform':readable_ogds_author},

        {'column': 'start',
         'column_title': _(u'label_start', default=u'Start'),
         'transform': helper.readable_date},

        {'column': 'end',
         'column_title': _(u'label_end', default=u'End'),
         'transform': helper.readable_date},
        {'column': 'filing_no',
         'column_title': _(u'filing_number', default=u'Filing Number')},
        )

    search_options = {'is_subdossier': False}

    enabled_actions = ['change_state',
                       'cut',
                       'copy',
                       'pdf_dossierlisting',
                       'move_items',
                       ]

    major_actions = ['change_state',
                     ]


class SubDossiers(Dossiers):

    grok.name('tabbedview_view-subdossiers')
    search_options = {'is_subdossier': True}


class Tasks(OpengeverCatalogListingTab):

    grok.name('tabbedview_view-tasks')

    columns= (
        ('', helper.draggable),
        ('', helper.path_checkbox),

        {'column': 'review_state',
         'column_title': _(u'label_review_state', default=u'Review state'),
         'transform': workflow_state},

        {'column': 'Title',
         'column_title': _(u'label_title', default=u'Title'),
         'sort_index' : 'sortable_title',
         'transform': linked},

        {'column': 'task_type',
         'column_title': _(u'label_task_type', 'Task Type'),
         'transform': task_type_helper},

        {'column': 'deadline',
         'column_title': _(u'label_deadline', 'Deadline'),
         'transform': helper.readable_date},

        {'column': 'date_of_completion',
         'column_title': _(u'label_date_of_completion', 'Date of Completion'),
         'transform': readable_date_set_invisibles},

        {'column': 'responsible',
         'column_title': _(u'label_responsible_task', 'Responsible'),
         'transform': readable_ogds_author},

        {'column': 'issuer',
         'column_title': _(u'label_issuer', 'Issuer'),
         'transform': readable_ogds_author},

        {'column': 'created',
         'column_title': _(u'label_issued_date', 'issued at'),
         'transform': helper.readable_date},

        {'column': 'client_id',
         'column_title': _('client_id', 'Client'),
         'transform': client_title_helper},

        {'column': 'sequence_number',
         'column_title': _(u'sequence_number', "Sequence Number"), },

        {'column':'containing_subdossier',
         'column_title':_('label_subdossier', default="Subdossier"),},
        )

    types = ['opengever.task.task', ]

    enabled_actions = [
        'change_state',
        'cut',
        'pdf_taskslisting',
        'move_items',
        ]

    major_actions = ['change_state',
                     ]


class Trash(Documents):
    grok.name('tabbedview_view-trash')

    types = ['opengever.dossier.dossier',
             'opengever.document.document',
             'opengever.task.task',
             'ftw.mail.mail', ]

    search_options = {'trashed': True}

    enabled_actions = ['untrashed', ]