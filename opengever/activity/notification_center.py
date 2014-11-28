from opengever.activity import Activity
from opengever.activity import Resource
from opengever.activity import Session
from opengever.activity import Watcher
from opengever.globalindex.oguid import Oguid


class NotificationCenter(object):

    def add_resource(self, oguid):
        resource = Resource(oguid=Oguid(id=oguid))
        Session.add(resource)
        return resource

    def fetch_resource(self, oguid):
        """Returns a resource by it's Oguid object or None when it does
        not exist.
        """
        return Resource.query.get_by_oguid(oguid)

    def add_watcher(self, user_id):
        watcher = Watcher(user_id=user_id)
        Session.add(watcher)
        return watcher

    def fetch_watcher(self, user_id):
        return Watcher.query.get_by_userid(user_id)

    def add_watcher_to_resource(self, oguid, userid):
        resource = self.fetch_resource(oguid)
        if not resource:
            resource = self.add_resource(oguid)

        resource.add_watcher(userid)

    def remove_watcher_from_resource(self, oguid, userid):
        watcher = self.fetch_watcher(userid)
        resource = self.fetch_resource(oguid)

        if not watcher:
            raise Exception('Watcher with userid {} not found.'.format(userid))

        if not resource:
            raise Exception('Resource with oguid {} not found.'.format(oguid))

        resource.remove_watcher(watcher)

    def get_watchers(self, oguid):
        resource = Resource.query.get_by_oguid(oguid)
        if not resource:
            return []

        return resource.watchers

    def add_acitivity(self, oguid, kind, title, actor_id, description=u''):
        resource = self.fetch_resource(oguid)

        if not resource:
            resource = self.add_resource(oguid)

        activity = Activity(resource=resource, kind=kind, title=title,
                            actor_id=actor_id, description=description)
        Session.add(activity)

        activity.notifiy()

        return activity
