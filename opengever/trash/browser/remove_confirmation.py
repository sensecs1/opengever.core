from five import grok
from opengever.trash import _
from Products.statusmessages.interfaces import IStatusMessage
from zope.interface import Interface


class RemoveConfirmation(grok.View):
    """Remove Confirmation View, allways displayed in a overlay.
    """
    grok.context(Interface)
    grok.name('remove_confirmation')
    grok.require('zope2.View')
    grok.template('remove_confirmation')

    def __call__(self):
        if not self.context.REQUEST.get('paths'):
            msg = _(u'error_no_documents_selected',
                    default=u'You have not selected any items')
            IStatusMessage(self.request).addStatusMessage(msg, type='error')

            return self.context.REQUEST.RESPONSE.redirect(
                '{}#trash'.format(self.context.absolute_url()))

        documents = self.get_selected_documents()
        # Remover().is_remove_allowed(documents)

        return super(RemoveConfirmation, self).__call__()

    def get_selected_documents(self):
        documents = []
        for path in self.context.REQUEST.get('paths'):
            documents.append(self.context.unrestrictedTraverse(path))

        return documents
