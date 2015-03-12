from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from opengever.ogds.base.utils import ogds_service
from plone import api
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile


class PloneNotificationMailer(object):

    def __init__(self):
        self.mailhost = api.portal.get_tool('MailHost')

        # This is required by ViewPageTemplateFile for
        # the html mail-template
        self.context = api.portal.get()
        self.request = self.context.REQUEST

    def dispatch_notification(self, notification):
        msg = self.prepare_mail(notification)
        self.send_mail(msg)

    def send_mail(self, msg):
        self.mailhost.send(msg)

    def prepare_mail(self, notification):
        msg = MIMEMultipart('alternative')

        actor = ogds_service().fetch_user(notification.activity.actor_id)
        msg['From'] = Header(u'{} <{}>'.format(actor.fullname(), actor.email),
                             'utf-8')

        recipient = ogds_service().fetch_user(notification.watcher.user_id)
        msg['To'] = recipient.email
        msg['Subject'] = Header(notification.activity.title, 'utf-8')

        html = self.prepare_html(notification)
        msg.attach(MIMEText(html.encode('utf-8'), 'html', 'utf-8'))

        return msg

    def prepare_html(self, notification):
        # Todo: solve circular dependency
        from opengever.activity.browser.resolve import ResolveNotificationView
        template = ViewPageTemplateFile("mail_templates/notification.pt")
        options = {
            'subject': notification.activity.title,
            'title': notification.activity.title,
            'kind': notification.activity.kind,
            'summary': notification.activity.summary,
            'description': notification.activity.description,
            'link': ResolveNotificationView.url_for(notification.notification_id)
        }

        return template(self, **options)