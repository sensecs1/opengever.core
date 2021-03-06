from opengever.base.model import Base
from opengever.base.oguid import Oguid
from opengever.meeting.model.query import CommitteeQuery
from opengever.ogds.base.utils import ogds_service
from plone import api
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import composite
from sqlalchemy.schema import Sequence


class Committee(Base):

    query_cls = CommitteeQuery

    __tablename__ = 'committees'
    __table_args__ = (UniqueConstraint('admin_unit_id', 'int_id'), {})

    committee_id = Column("id", Integer, Sequence("committee_id_seq"),
                          primary_key=True)

    admin_unit_id = Column(String(30), nullable=False)
    int_id = Column(Integer, nullable=False)
    oguid = composite(Oguid, admin_unit_id, int_id)
    title = Column(String(256))
    physical_path = Column(String(256), nullable=False)

    def __repr__(self):
        return '<Committee {}>'.format(repr(self.title))

    def get_admin_unit(self):
        return ogds_service().fetch_admin_unit(self.admin_unit_id)

    def get_link(self):
        url = self.get_url()
        if not url:
            return ''

        link = u'<a href="{0}" title="{1}">{1}</a>'.format(url, self.title)
        transformer = api.portal.get_tool('portal_transforms')
        return transformer.convertTo('text/x-html-safe', link).getData()

    def get_url(self, admin_unit=None):
        admin_unit = admin_unit or self.get_admin_unit()
        if not admin_unit:
            return None

        return '/'.join((admin_unit.public_url, self.physical_path))
