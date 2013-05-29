from opengever.mail.mail import IOGMailMarker
from opengever.testing import Builder
from opengever.testing import FunctionalTestCase
import os


MAIL_DATA = open(
    os.path.join(os.path.dirname(__file__), 'mail.txt'), 'r').read()


class TestOGMailAddition(FunctionalTestCase):
    use_browser = True

    def setUp(self):
        super(TestOGMailAddition, self).setUp()
        self.grant('Contributor', 'Editor', 'Member', 'Manager')

    def test_og_mail_behavior(self):
        mail = Builder("mail").create()
        self.assertTrue(
            IOGMailMarker.providedBy(mail),
            'ftw mail obj does not provide the OGMail behavior interface.')

    def test_title_accessor(self):
        mail = Builder("mail").create()
        self.assertEquals(u'[No Subject]', mail.title)
        self.assertEquals('[No Subject]', mail.Title())

        mail = Builder("mail").with_message(MAIL_DATA).create()

        self.assertEquals(u'Die B\xfcrgschaft', mail.title)
        self.assertEquals('Die B\xc3\xbcrgschaft', mail.Title())

    def test_mail_behavior(self):
        mail = Builder("mail").with_message(MAIL_DATA).create()

        self.browser.open('%s/edit' % mail.absolute_url())
        self.browser.getControl(
            name='form.widgets.IOGMail.title').value = 'hanspeter'
        self.browser.getControl(name='form.buttons.save').click()

        self.assertEquals(u'hanspeter', mail.title)
        self.assertEquals('hanspeter', mail.Title())