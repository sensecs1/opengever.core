from opengever.meeting import _
from plone.app.textfield import RichText
from plone.dexterity.content import Container
from plone.directives import form
from plone.formwidget.contenttree import ObjPathSourceBinder
from z3c.relationfield.schema import RelationChoice
from zope import schema


class IMeetingItem(form.Schema):

    form.fieldset(
        u'common',
        label=_(u'fieldset_common', default=u'Common'),
        fields=[u'proposal', 'resolution', 'transcript', 'votes'],
        )

    proposal = RelationChoice(
        title=_(u'label_proposal', default=u'Proposal'),
        source=ObjPathSourceBinder(
            object_provides='opengever.meeting.proposal.IMeetingProposal',
            navigation_tree_query={
                'object_provides': [
                    'opengever.repository.repositoryroot.IRepositoryRoot',
                    'opengever.repository.repositoryfolder.' +
                    'IRepositoryFolderSchema',
                    'opengever.dossier.behaviors.dossier.IDossierMarker',
                ]
                }),
        required=True,
    )

    resolution = RichText(
         title=_(u'label_resolution', default=u'Resolution'),
         required=False,
    )

    transcript = RichText(
        title=_(u'label_transcript', default=u'Transcript'),
        required=False,
    )

    votes = schema.TextLine(
        title=_(u'label_votes', default=u'Votes'),
        required=False,
    )


class MeetingItem(Container):

    def Title(self):
        return self.proposal.to_object.Title()
