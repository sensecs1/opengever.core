from datetime import datetime
from datetime import time
from opengever.base.model import Base
from opengever.meeting.model.query import MembershipQuery
from plone import api
from sqlalchemy import Column
from sqlalchemy import Date
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.orm import relationship


class Membership(Base):
    """Associate members with their commmission for a certain timespan.

    """
    query_cls = MembershipQuery

    __tablename__ = 'memberships'

    date_from = Column(Date, primary_key=True)
    date_to = Column(Date, nullable=False)

    committee_id = Column(Integer, ForeignKey('committees.id'),
                          primary_key=True)
    committee = relationship("Committee", backref="memberships")
    member_id = Column(Integer, ForeignKey('members.id'),
                       primary_key=True)
    member = relationship("Member", backref="memberships")
    role = Column(String(256))

    def __repr__(self):
        return '<Membership {} in {} {}:{}>'.format(
            repr(self.member.fullname),
            repr(self.committee.title),
            self.date_from,
            self.date_to)

    def format_date_from(self):
        return self._format_date(self.date_from)

    def format_date_to(self):
        if not self.date_to:
            return ''

        return self._format_date(self.date_to)

    def _format_date(self, date):
        return api.portal.get_localized_time(
            datetime=datetime.combine(date, time()))

    def title(self):
        return self.member.fullname
