from opengever.activity.browser.resolve import ResolveNotificationView
from opengever.activity.utils import is_activity_feature_enabled
from opengever.activity.utils import notification_center
from plone.app.layout.viewlets import common
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile


class NotificationViewlet(common.ViewletBase):

    index = ViewPageTemplateFile('notification.pt')
    notifications = []

    def available(self):
        return is_activity_feature_enabled()

    def num_unread(self):
        notifications = self.fetch_notifications()
        return len(notifications)

    def fetch_notifications(self):
        if not self.notifications:
            center = notification_center()
            self.notifications = center.get_current_users_notifications(
                only_unread=True, limit=10)

        return self.notifications

    def get_notifications(self):
        notifications = []

        for notification in self.fetch_notifications():
            notifications.append({
                'kind': notification.activity.kind,
                'title': notification.activity.title,
                'summary': notification.activity.summary,
                'created': notification.activity.created,
                'link': ResolveNotificationView.url_for(
                    notification.notification_id),
                'read': notification.read,
                'id': notification.notification_id})

        return notifications

    @property
    def read_url(self):
        return '{}/notifications/read'.format(self.context.absolute_url())