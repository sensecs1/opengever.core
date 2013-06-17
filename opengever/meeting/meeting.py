from opengever.meeting import _
from plone.directives import form
from zope import schema
from plone.dexterity.content import Container


class IMeeting(form.Schema):

    form.fieldset(
        u'common',
        label=_(u'fieldset_common', default=u'Common'),
        fields=[u'date', 'participants'],
        )

    date = schema.Date(
         title=_(u'label_date', default=u'Date'),
         required=True,
         )

    participants = schema.List(
        title=_(u'label_participants', default=u'Participants'),
        required=True,
        value_type=schema.Choice(
            title=_(u"label_participant", default="Participant"),
            vocabulary=u'opengever.ogds.base.AssignedUsersVocabulary',
            required=True,
        )
    )



class Meeting(Container):

    def Title(self):
        return 'Meeeting from %s' % (self.date.strftime('%d.%m.%Y'))
