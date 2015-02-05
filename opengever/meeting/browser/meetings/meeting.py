from ftw.datepicker.widget import DatePickerFieldWidget
from opengever.base.model import create_session
from opengever.meeting import _
from opengever.meeting.browser.meetings.agendaitem import DeleteAgendaItem
from opengever.meeting.browser.meetings.agendaitem import ScheduleParagraph
from opengever.meeting.browser.meetings.agendaitem import ScheduleSubmittedProposal
from opengever.meeting.browser.meetings.agendaitem import ScheduleText
from opengever.meeting.browser.meetings.agendaitem import UpdateAgendaItemOrder
from opengever.meeting.browser.meetings.meetinglist import MeetingList
from opengever.meeting.browser.meetings.preprotocol import EditPreProtocol
from opengever.meeting.browser.meetings.transitions import MeetingTransitionController
from opengever.meeting.model import Meeting
from plone.autoform.form import AutoExtensibleForm
from plone.directives import form
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from z3c.form import button
from z3c.form import field
from z3c.form.form import AddForm
from z3c.form.form import EditForm
from z3c.form.interfaces import HIDDEN_MODE
from zExceptions import NotFound
from zope import schema
from zope.interface import implements
from zope.publisher.interfaces import IPublishTraverse
from zope.publisher.interfaces.browser import IBrowserView


class IMeetingModel(form.Schema):
    """Meeting model schema interface."""

    committee = schema.Choice(
        title=_('label_committee', default=u'Committee'),
        source='opengever.meeting.CommitteeVocabulary',
        required=True)

    location = schema.TextLine(
        title=_(u"label_location", default=u"Location"),
        max_length=256,
        required=False)

    form.widget(date=DatePickerFieldWidget)
    date = schema.Date(
        title=_('label_date', default=u"Date"),
        required=True)

    start_time = schema.Time(
        title=_('label_start_time', default=u'Start time'),
        required=False)

    end_time = schema.Time(
        title=_('label_end_time', default=u'End time'),
        required=False)


class AddMeeting(AutoExtensibleForm, AddForm):

    ignoreContext = True
    schema = IMeetingModel

    def updateWidgets(self):
        super(AddMeeting, self).updateWidgets()

        committee_id = self.context.load_model().committee_id
        self.widgets['committee'].mode = HIDDEN_MODE
        self.widgets['committee'].value = (str(committee_id), )

    def __init__(self, context, request):
        super(AddMeeting, self).__init__(context, request)
        self._created_object = None
        self.request.set('disable_border', True)  # disables the edit bar.

    def create(self, data):
        return Meeting(**data)

    def add(self, obj):
        session = create_session()
        session.add(obj)
        session.flush()  # required to create an autoincremented id
        self._created_object = obj

    def nextURL(self):
        return MeetingList.url_for(self.context, self._created_object)


class EditMeeting(EditForm):

    ignoreContext = True
    fields = field.Fields(IMeetingModel)

    is_model_view = True
    is_model_edit_view = True

    def __init__(self, context, request, model):
        super(EditMeeting, self).__init__(context, request)
        self.model = model
        self._has_finished_edit = False

    def inject_initial_data(self):
        if self.request.method != 'GET':
            return

        prefix = 'form.widgets.'
        values = self.model.get_edit_values(self.fields.keys())

        for fieldname, value in values.items():
            self.request[prefix + fieldname] = value

    def updateWidgets(self):
        self.inject_initial_data()
        super(EditMeeting, self).updateWidgets()

        committee_id = self.context.load_model().committee_id
        self.widgets['committee'].mode = HIDDEN_MODE
        self.widgets['committee'].value = (str(committee_id), )

    def applyChanges(self, data):
        self.model.update_model(data)
        # pretend to always change the underlying data
        self._has_finished_edit = True
        return True

    # this renames the button but otherwise preserves super's behavior
    @button.buttonAndHandler(_('Save'), name='save')
    def handleApply(self, action):
        # self as first argument is required by the decorator
        super(EditMeeting, self).handleApply(self, action)

    def nextURL(self):
        return MeetingList.url_for(self.context, self.model)

    def render(self):
        if self._has_finished_edit:
            return self.request.response.redirect(self.nextURL())
        return super(EditMeeting, self).render()


class MeetingView(BrowserView):

    template = ViewPageTemplateFile('templates/meeting.pt')
    implements(IBrowserView, IPublishTraverse)

    is_model_view = True
    is_model_edit_view = False

    mapped_actions = {
        'edit': EditMeeting,
        'delete_agenda_item': DeleteAgendaItem,
        'schedule_paragraph': ScheduleParagraph,
        'schedule_proposal': ScheduleSubmittedProposal,
        'schedule_text': ScheduleText,
        'pre_protocol': EditPreProtocol,
        'meetingtransitioncontroller': MeetingTransitionController,
        'update_agenda_item_order': UpdateAgendaItemOrder,
    }

    def __init__(self, context, request, meeting):
        super(MeetingView, self).__init__(context, request)
        self.model = meeting

    def __call__(self):
        return self.template()

    def transition_url(self, transition):
        return MeetingTransitionController.url_for(
            self.context, self.model, transition.name)

    def unscheduled_proposals(self):
        return self.context.get_unscheduled_proposals()

    def publishTraverse(self, request, name):
        if name in self.mapped_actions:
            view_class = self.mapped_actions.get(name)
            return view_class(self.context, self.request, self.model)
        raise NotFound

    def url_schedule_proposal(self):
        return ScheduleSubmittedProposal.url_for(self.context, self.model)

    def url_schedule_text(self):
        return ScheduleText.url_for(self.context, self.model)

    def url_schedule_paragraph(self):
        return ScheduleParagraph.url_for(self.context, self.model)

    def url_delete_agenda_item(self, agenda_item):
        return DeleteAgendaItem.url_for(self.context, self.model, agenda_item)

    def url_pre_protocol(self):
        return EditPreProtocol.url_for(self.context, self.model)

    def url_update_agenda_item_order(self):
        return UpdateAgendaItemOrder.url_for(self.context, self.model)

    def transitions(self):
        return self.model.get_state().get_transitions()

    def agenda_items(self):
        return self.model.agenda_items
