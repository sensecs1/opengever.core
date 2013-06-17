# from Acquisition import aq_inner, aq_parent
# from plone.dexterity.content import Item
from five import grok
from opengever.base.source import DossierPathSourceBinder
from opengever.meeting import _
from opengever.ogds.base.autocomplete_widget import AutocompleteFieldWidget
from plone.directives import dexterity
from plone.directives import form
from z3c.relationfield.schema import RelationChoice, RelationList
from zope import schema


class IMeetingProposal(form.Schema):

    form.fieldset(
        u'common',
        label=_(u'fieldset_common', default=u'Common'),
        fields=[u'title',
                'description',
                'documents',
                'responsible'],
        )

    title = schema.TextLine(
         title=_(u'label_title', default=u'Title'),
         required=False,
    )

    description = schema.Text(
         title=_(u'label_description', default=u'Description'),
         required=False,
    )

    documents = RelationList(
        title=_(u'label_documents', default=u'Documents'),
        default=[],
        value_type=RelationChoice(
            title=u"Document",
            source=DossierPathSourceBinder(
                portal_type=("opengever.document.document", "ftw.mail.mail"),
                navigation_tree_query={
                    'object_provides':
                    ['opengever.dossier.behaviors.dossier.IDossierMarker',
                     'opengever.document.document.IDocumentSchema',
                     'opengever.task.task.ITask',
                     'ftw.mail.mail.IMail', ],
                }),
            ),
        required=False,
    )

    form.widget(responsible=AutocompleteFieldWidget)
    responsible = schema.Choice(
        title=_(u"label_responsible_board", default=u"Responsible board"),
        description=_(u"help_responsible", default=""),
        vocabulary=u'opengever.ogds.base.BoardsVocabularyFactory',
        required=True,
        )


@form.default_value(field=IMeetingProposal['title'])
def generate_proposal_title(data):
    return u'TA: %s' % (data.context.title)


class AddForm(dexterity.AddForm):
    grok.name('opengever.meeting.proposal')

    def update(self):
        paths = self.request.get('paths', [])
        if paths:
            self.request.set('form.widgets.documents', paths)

        return super(AddForm, self).update()
