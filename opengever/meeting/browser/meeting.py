from five import grok
from opengever.meeting.meeting import IMeeting
from plone.directives.dexterity import DisplayForm


class MeetingView(DisplayForm):
    grok.context(IMeeting)
    grok.name('view')
    grok.require("zope2.View")

    def get_meeting_items(self):

        return self.context.listFolderContents()


class MeetingItemOrderSaveView(grok.View):
    grok.context(IMeeting)
    grok.name('meeting_item_order_save')
    grok.require("zope2.View")

    def render(self):
        ids = self.request.get('ids', None)
        if not ids:
            raise AttributeError

        ids = ids.split(',')
        for position, _id in enumerate(ids):
            obj = self.context.get(_id)
            self.context.moveObject(_id, position)
            obj.reindexObject(idxs=['getObjPositionInParent'])
        return 'OK'
