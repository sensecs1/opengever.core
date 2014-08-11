from DateTime import DateTime as ZopeDateTime
from opengever.globalindex import Session
from opengever.globalindex.model import Base
from opengever.globalindex.model.query import TaskQuery
from opengever.globalindex.oguid import Oguid
from opengever.ogds.base.actor import Actor
from opengever.ogds.base.utils import get_current_admin_unit
from opengever.ogds.base.utils import ogds_service
from opengever.tabbedview.helper import overdue_date_helper
from plone import api
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import Date
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy import UniqueConstraint
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import backref
from sqlalchemy.orm import composite
from sqlalchemy.orm import relation
from sqlalchemy.orm import relationship
from sqlalchemy.schema import Sequence
from sqlalchemy.sql import functions
from zope.i18n import translate


class Task(Base):
    """docstring for Task"""

    query_cls = TaskQuery

    MAX_TITLE_LENGTH = 256
    MAX_BREADCRUMB_LENGTH = 512

    __tablename__ = 'tasks'
    __table_args__ = (UniqueConstraint('admin_unit_id', 'int_id'), {})

    task_id = Column("id", Integer, Sequence("task_id_seq"), primary_key=True)

    admin_unit_id = Column(String(30), index=True, nullable=False)
    int_id = Column(Integer, index=True, nullable=False)

    oguid = composite(Oguid, admin_unit_id, int_id)

    title = Column(String(MAX_TITLE_LENGTH))
    text = Column(Text)
    breadcrumb_title = Column(String(MAX_BREADCRUMB_LENGTH))
    physical_path = Column(String(256))
    review_state = Column(String(50))
    icon = Column(String(50))

    responsible = Column(String(32), index=True)
    issuer = Column(String(32), index=True)

    task_type = Column(String(50), index=True)
    is_subtask = Column(Boolean(), default=False)

    reference_number = Column(String(100))
    sequence_number = Column(Integer, index=True, nullable=False)
    dossier_sequence_number = Column(Integer, index=True)
    containing_dossier = Column(String(512))
    containing_subdossier = Column(String(512))

    created = Column(DateTime, default=functions.now())
    modified = Column(DateTime)
    deadline = Column(Date)
    completed = Column(Date)

    # XXX shit, this should be ...org_unit_ID
    issuing_org_unit = Column(String(30), index=True, nullable=False)
    assigned_org_unit = Column(String(30), index=True, nullable=False)

    predecessor_id = Column(Integer, ForeignKey('tasks.id'))
    successors = relationship(
        "Task",
        backref=backref('predecessor', remote_side=task_id),
        cascade="delete")

    _principals = relation('TaskPrincipal', backref='task',
                           cascade='all, delete-orphan')
    principals = association_proxy('_principals', 'principal')

    def __init__(self, int_id, admin_unit_id, **kwargs):
        super(Task, self).__init__(**kwargs)
        self.admin_unit_id = admin_unit_id
        self.int_id = int_id

    def __repr__(self):
        return "<Task %s@%s>" % (self.int_id, self.admin_unit_id)

    @property
    def id(self):
        return self.task_id

    def get_admin_unit(self):
        return ogds_service().fetch_admin_unit(self.admin_unit_id)

    def get_issuing_org_unit(self):
        return ogds_service().fetch_org_unit(self.issuing_org_unit)

    def get_assigned_org_unit(self):
        return ogds_service().fetch_org_unit(self.assigned_org_unit)

    def sync_with(self, plone_task):
        """Sync this task instace with its corresponding plone taks.

        """
        self.title = plone_task.safe_title
        self.text = plone_task.text
        self.breadcrumb_title = plone_task.get_breadcrumb_title(
            self.MAX_BREADCRUMB_LENGTH)
        self.physical_path = plone_task.get_physical_path()
        self.review_state = plone_task.get_review_state()
        self.icon = plone_task.getIcon()
        self.responsible = plone_task.responsible
        self.issuer = plone_task.issuer
        self.deadline = plone_task.deadline
        self.completed = plone_task.date_of_completion
        # we need to have python datetime objects for make it work with sqlite
        self.modified = plone_task.modified().asdatetime().replace(tzinfo=None)
        self.task_type = plone_task.task_type
        self.is_subtask = plone_task.get_is_subtask()
        self.sequence_number = plone_task.get_sequence_number()
        self.reference_number = plone_task.get_reference_number()
        self.containing_dossier = plone_task.get_containing_dossier()
        self.dossier_sequence_number = plone_task.get_dossier_sequence_number()
        self.assigned_org_unit = plone_task.responsible_client
        self.principals = plone_task.get_principals()
        self.predecessor = self.query_predecessor(
            *plone_task.get_predecessor_ids())
        self.containing_subdossier = plone_task.get_containing_subdossier()

    # XXX move me to task query
    def query_predecessor(self, admin_unit_id, pred_init_id):
        if not (admin_unit_id or pred_init_id):
            return None

        return Session.query(Task).filter_by(
            admin_unit_id=admin_unit_id, int_id=pred_init_id).first()

    # XXX rename me, this should be get_issuer_link
    def get_issuer_label(self):
        actor = Actor.lookup(self.issuer)
        org_unit = ogds_service().fetch_org_unit(self.issuing_org_unit)
        return org_unit.prefix_label(actor.get_link())

    @property
    def is_forwarding(self):
        return self.task_type == 'forwarding_task_type'

    # XXX rename me, this should be get_responsible_link
    def get_responsible_label(self):
        actor = Actor.lookup(self.responsible)
        org_unit = ogds_service().fetch_org_unit(self.assigned_org_unit)
        return org_unit.prefix_label(actor.get_link())

    def get_state_label(self):
        return "<span class=wf-{}>{}</span>".format(
            self.review_state,
            translate(self.review_state, domain='plone',
                      context=api.portal.get().REQUEST),
        )

    def get_deadline_label(self):
        return overdue_date_helper(self, self.deadline)

    def _date_to_zope_datetime(self, date):
        if not date:
            return None
        return ZopeDateTime(date.year, date.month, date.day)

    def get_deadline(self):
        return self._date_to_zope_datetime(self.deadline)

    def get_completed(self):
        return self._date_to_zope_datetime(self.completed)

    def has_access(self, member):
        if not member:
            return False

        principals = set(member.getGroups() + [member.getId()])
        allowed_principals = set(self.principals)
        return len(principals & allowed_principals) > 0

    # XXX Todo: the css_class helper should moved to the task class itself,
    # so that the css_class parameter is not necessary anymore.
    def get_link(self, css_class):
        admin_unit = self.get_admin_unit()
        if not admin_unit:
            return u'<span class="{}">{}</span>'.format(css_class, self.title)

        url = '/'.join((admin_unit.public_url, self.physical_path))
        # If the target is on a different client we need to make a popup
        if self.admin_unit_id != get_current_admin_unit().id():
            link_target = u' target="_blank"'
        else:
            link_target = u''

        # create breadcrumbs including the (possibly remote) client title
        breadcrumb_titles = u"[{}] > {}".format(admin_unit.title,
                                               self.breadcrumb_title)

        # Client and user info
        assigned_org_unit = ogds_service().fetch_org_unit(
            self.assigned_org_unit)
        info_html = u' <span class="discreet">({})</span>'.format(
            assigned_org_unit.prefix_label(
                Actor.lookup(self.responsible).get_label()))

        # Link to the task object
        task_html = u'<span class="{}">{}</span>'.format(css_class, self.title)

        # Render the full link if we have acccess
        if self.has_access(api.user.get_current()):
            inner_html = u'<a href="{}"{} title="{}">{}</a> {}'.format(
                url,
                link_target,
                breadcrumb_titles,
                task_html,
                info_html)
        else:
            inner_html = u'{} {}'.format(task_html, info_html)

        # Add the task-state css and return it
        return self._task_state_wrapper(inner_html)

    def _task_state_wrapper(self, text):
        """ Wrap a span-tag around the text with the status-css class
        """
        return u'<span class="wf-%s">%s</span>' % (self.review_state, text)


class TaskPrincipal(Base):
    __tablename__ = 'task_principals'

    principal = Column(String(255), primary_key=True)
    task_id = Column(Integer, ForeignKey('tasks.id'),
                     primary_key=True)

    def __init__(self, principal):
        self.principal = principal

    def __repr__(self):
        return "<TaskPrincipal %s for %s>" % (self.principal, str(self.task))
