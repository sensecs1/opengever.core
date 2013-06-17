from five import grok
from opengever.meeting import _
from opengever.ogds.base.utils import create_session
from opengever.ogds.models.board import Board
from plone.i18n.normalizer.interfaces import IIDNormalizer
from plone.z3cform import layout
from z3c.form import form, field, button
from zope import schema
from zope.component import getUtility
from zope.interface import Interface


class IAddBoardFormSchema(Interface):

    title = schema.TextLine(
        title=_(u'label_title', default=u'Title'),
        required=True)

    description = schema.Text(
        description=_(u"label_description", default=u"Description"),
        required=True,
        )


class AddBoardForm(form.Form):

    fields = field.Fields(IAddBoardFormSchema)
    ignoreContext = True
    label = _(u'label_add_board', default=u'Add Board')

    @button.buttonAndHandler(_(u'button_add', default=u'Add'))
    def add_board(self, action):
        data, errors = self.extractData()

        if not errors:
            session = create_session()
            boardid = getUtility(IIDNormalizer).normalize(data.get('title'))
            board = Board(boardid,
                          title=data.get('title'),
                          description=data.get('description'))
            session.add(board)

            self.request.RESPONSE.redirect(self.context.absolute_url())


class AddBoardView(layout.FormWrapper, grok.View):

    grok.context(Interface)
    grok.require('zope2.View')
    grok.name('add_board')
    form = AddBoardForm
