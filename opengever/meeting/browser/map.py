from Acquisition import aq_parent, aq_inner
from Products.CMFCore.utils import getToolByName
from five import grok
from opengever.meeting.proposal import IMeetingProposal
from opengever.ogds.base.interfaces import IContactInformation
from plone.app.uuid.utils import uuidToObject
from plone.dexterity.utils import createContentInContainer
from plone.uuid.interfaces import IUUID
from z3c.relationfield import RelationValue
from zope.app.intid.interfaces import IIntIds
from zope.component import getUtility
from zope.event import notify
from zope.interface import Interface
from zope.lifecycleevent import ObjectCreatedEvent, ObjectAddedEvent

PROPOSAL_OPEN_STATE = 'proposal-state-open'
PROPOSAL_PLANED_STATE = 'proposal-state-planed'
PROPOSAL_OPEN_TRANSITION = 'proposal-transition-planed-open'


class MapProposal(grok.View):
    grok.name('map_proposals')
    grok.context(Interface)
    grok.require("zope2.View")

    def get_boards(self):
       info = getUtility(IContactInformation)
       return info.get_boards()

    def get_meetings(self, boardid=None):
        catalog = getToolByName(self.context, 'portal_catalog')
        if boardid:
            return catalog(portal_type='opengever.meeting.meeting',
                           responsible=boardid)
        else:
            return catalog(portal_type='opengever.meeting.meeting')


    def get_not_mapped_proposals(self, boardid=None):
        catalog = getToolByName(self.context, 'portal_catalog')
        query = {'portal_type':'opengever.meeting.proposal',
                 'review_state': PROPOSAL_OPEN_STATE}

        if boardid:
            query['responsible'] = boardid
        return catalog(query)

    def get_meeting_items(self, meeting):
        catalog = getToolByName(self.context, 'portal_catalog')
        query = {'portal_type':'opengever.meeting.item',
                 'path': meeting.getPath(),
                 'depth': -1,
                 'sort_on': 'getObjPositionInParent'}

        return catalog(query)


class MapProposalSaveView(grok.View):
    grok.context(Interface)
    grok.name('map_proposal_save_view')
    grok.require("zope2.View")

    def render(self):
        meeting_uid = self.request.get('meeting', None)
        item_uid = self.request.get('item', None)
        ids = self.request.get('ids', None)
        ids = ids.split(',')

        obj = uuidToObject(item_uid)

        if meeting_uid == 'no_map':
            return self.drop_meeting_item(obj)

        elif IMeetingProposal.providedBy(obj):
            meeting = uuidToObject(meeting_uid)
            item = self.create_meeting_item(meeting, obj)
            self.replace_uid(ids, item_uid, item)

            self.update_order(meeting, ids)
            return IUUID(item)

        else:
            meeting = uuidToObject(meeting_uid)
            if aq_parent(aq_inner(obj)) == meeting:
                self.update_order(meeting, ids)
                return 'OK'
            else:
                self.move_meeting_item(obj, meeting)
                self.update_order(meeting, ids)

    def replace_uid(self, ids, old, item):
        # replace old uid with uid of the new object
        for i, _id in enumerate(ids):
            if _id == old:
                ids[i] = IUUID(item)

    def move_meeting_item(self, item, target):
        source = aq_parent(aq_inner(item))
        target.manage_pasteObjects(
            source.manage_cutObjects(item.getId()))

    def create_meeting_item(self, meeting, proposal):
        intids = getUtility(IIntIds)
        item = createContentInContainer(
            meeting, 'opengever.meeting.item',
            proposal=RelationValue(intids.getId(proposal)),)

        notify(ObjectCreatedEvent(item))
        notify(ObjectAddedEvent(item))

        return item

    def drop_meeting_item(self, obj):
        wf_tool = getToolByName(obj, 'portal_workflow')
        meeting = aq_parent(aq_inner(obj))
        proposal = obj.proposal.to_object

        meeting.manage_delObjects([obj.getId()])
        if wf_tool.getInfoFor(proposal, 'review_state') == PROPOSAL_PLANED_STATE:
            wf_tool.doActionFor(proposal, PROPOSAL_OPEN_TRANSITION)

        return IUUID(proposal)

    def update_order(self, meeting, ids):
        for position, uid in enumerate(ids):
            obj = uuidToObject(uid)
            meeting.moveObject(obj.id, position)
            obj.reindexObject(idxs=['getObjPositionInParent'])
