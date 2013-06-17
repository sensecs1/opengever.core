from five import grok
from ftw.table import helper
from opengever.meeting import _
from opengever.tabbedview.browser.tabs import OpengeverCatalogListingTab
from opengever.tabbedview.helper import linked
# from opengever.tabbedview.helper import readable_ogds_board


class Meetings(OpengeverCatalogListingTab):
    """List all meeting items.
    """

    grok.name('tabbedview_view-meetings')

    types = ['opengever.meeting.meeting']

    columns = (

        {'column': '',
         'column_title': '',
         'transform': helper.path_checkbox,
         'width': 30},

        {'column': 'Title',
         'column_title': _(u'label_title', default=u'Title'),
         'sort_index': 'sortable_title',
         'transform': linked},
    )


class Proposals(OpengeverCatalogListingTab):
    grok.name('tabbedview_view-proposals')

    # depth = 0
    types = ['opengever.meeting.proposal']

    columns = (
        {'column': '',
         'column_title': '',
         'transform': helper.path_checkbox,
         'width': 30},

        {'column': 'Title',
         'column_title': _(u'label_title', default=u'Title'),
         'sort_index': 'sortable_title',
         'transform': linked},

        {'column': 'responsible',
         'column_title': _(u'label_responsible_board',
                           default=u'Responsible board'),
         }
         # 'transform': readable_ogds_board}
    )


    def update_config(self):
        super(Proposals, self).update_config()
        plone = self.context.restrictedTraverse('@@plone_portal_state')
        self.filter_path = plone.navigation_root_path()
