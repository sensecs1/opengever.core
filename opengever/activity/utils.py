from opengever.activity import is_activity_feature_enabled
from opengever.activity.mail import PloneNotificationMailer
from opengever.activity.notification_center import NotificationCenter
from opengever.base.oguid import Oguid
from plone import api


def notification_center():
    if not is_activity_feature_enabled():
        return DisabledNotificationCenter()

    return PloneNotificationCenter()


class PloneNotificationCenter(NotificationCenter):
    """The PloneNotificationCenter is a wrapper of the NotificationCenter,
    which provides some helper methods for easier access.
    """

    def __init__(self):
        dispatchers = [PloneNotificationMailer()]
        super(PloneNotificationCenter, self).__init__(dispatchers)

    def add_watcher_to_resource(self, obj, userid):
        oguid = Oguid.for_object(obj)
        super(PloneNotificationCenter, self).add_watcher_to_resource(oguid, userid)

    def remove_watcher_from_resource(self, obj, userid):
        oguid = Oguid.for_object(obj)
        super(PloneNotificationCenter, self).remove_watcher_from_resource(
            oguid, userid)

    def add_activity(self, obj, kind, title, summary, actor_id, description=u''):
        oguid = Oguid.for_object(obj)

        return super(PloneNotificationCenter, self).add_activity(
            oguid, kind, title, summary, actor_id, description=description)

    def get_watchers(self, obj):
        oguid = Oguid.for_object(obj)
        return super(PloneNotificationCenter, self).get_watchers(oguid)

    def get_current_users_notifications(self, only_unread=False, limit=None):
        return super(PloneNotificationCenter, self).get_users_notifications(
            api.user.get_current().getId(),
            only_unread=only_unread,
            limit=limit)


class DisabledNotificationCenter(NotificationCenter):

    def add_resource(self, oguid):
        pass

    def fetch_resource(self, oguid):
        return None

    def add_watcher(self, user_id):
        pass

    def fetch_watcher(self, user_id):
        return None

    def add_watcher_to_resource(self, obj, userid):
        pass

    def remove_watcher_from_resource(self, obj, userid):
        pass

    def get_watchers(self, obj):
        return []

    def add_activity(self, obj, kind, title, summary, actor_id, description=u''):
        pass

    def get_users_notifications(self, userid, only_unread=False, limit=None):
        return []

    def mark_notification_as_read(self, notification_id):
        pass

    def get_current_users_notifications(self, only_unread=False, limit=None):
        return []