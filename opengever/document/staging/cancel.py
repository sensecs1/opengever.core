
from five import grok
from zope.interface import Interface

from opengever.document.staging.manager import ICheckinCheckoutManager

class CancelCheckout(grok.CodeView):
    grok.context(Interface)
    grok.require('zope2.View')
    grok.name('cancel_document_checkouts')

    def render(self):
        for obj in self.objects:
            manager = ICheckinCheckoutManager(obj)
            manager.cancel()
        response = self.request.RESPONSE
        redirect_url = self.request.get('orig_template', None)
        if not redirect_url:
            redirect_url = self.request.get('HTTP_REFERER', None)
        if not redirect_url:
            redirect_url = '.'
        return response.redirect(redirect_url)

    @property
    def objects(self):
        lookup = lambda p:self.context.restrictedTraverse(str(p))
        paths = self.request.get('paths')
        return [lookup(p) for p in paths]
