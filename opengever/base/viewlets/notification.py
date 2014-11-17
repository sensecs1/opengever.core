from plone.app.layout.viewlets import common
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile


class Notification(common.ViewletBase):

    index = ViewPageTemplateFile('notification.pt')

    def num_unread(self):
        return 3

    def unread(self):
        return self.num_unread() > 0

    def get_notifications(self):
        return [
            {'type': 'Dossier',
             'creation': 'vor 3 Minuten',
             'location': 'Einf\xc3\xbchrung GEVER',
             'summary': 'Abgeschlossen durch: Christian Schneider'},
            {'type': 'Aufgabe',
             'creation': 'vor 2 Stunden',
             'location': 'Budget 2015 pr\xc3\xbcfen',
             'summary': 'Zugewiesen durch: Franz Hofstetter'},
            {'type': 'Aufgabe',
             'creation': 'vor 3 Stunden',
             'location': 'Sitzungsprotokoll genehmigen',
             'summary': 'Abgeschlossen durch: Alice Kaufmann'},
        ]
