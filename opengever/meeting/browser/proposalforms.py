from five import grok
from opengever.meeting.form import ModelAddForm
from opengever.meeting.form import ModelEditForm
from opengever.meeting.proposal import IProposal
from opengever.meeting.proposal import ISubmittedProposal
from opengever.meeting.proposal import Proposal
from opengever.meeting.proposal import SubmittedProposal
from plone.directives import dexterity
from z3c.form import field
from z3c.form.interfaces import HIDDEN_MODE


class ProposalEditForm(ModelEditForm, dexterity.EditForm):

    grok.context(IProposal)
    fields = field.Fields(Proposal.model_schema, ignoreContext=True)
    content_type = Proposal


class SubmittedProposalEditForm(ModelEditForm, dexterity.EditForm):

    grok.context(ISubmittedProposal)
    fields = field.Fields(SubmittedProposal.model_schema, ignoreContext=True)
    content_type = Proposal

    def updateWidgets(self):
        super(SubmittedProposalEditForm, self).updateWidgets()
        self.widgets['relatedItems'].mode = HIDDEN_MODE


class AddForm(ModelAddForm, dexterity.AddForm):

    grok.name('opengever.meeting.proposal')
    content_type = Proposal
    fields = field.Fields(Proposal.model_schema)
