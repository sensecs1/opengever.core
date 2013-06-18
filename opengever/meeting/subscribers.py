from Products.CMFCore.utils import getToolByName
from five import grok
from opengever.meeting.item import IMeetingItem
from zope.app.container.interfaces import IObjectAddedEvent

PLANED_TRANSITION = 'proposal-transition-open-planed'
PLANED_STATE = 'proposal-state-planed'

@grok.subscribe(IMeetingItem, IObjectAddedEvent)
def do_planed_transition(context, event):
    """It marks referenced proposal as planed,
    do the planed transitions for the referenced proposal."""

    wf_tool = getToolByName(context, 'portal_workflow')
    proposal = context.proposal.to_object

    if wf_tool.getInfoFor(proposal, 'review_state') != PLANED_STATE:
        wf_tool.doActionFor(proposal, PLANED_TRANSITION)
