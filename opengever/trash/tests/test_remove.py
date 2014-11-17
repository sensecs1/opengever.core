from ftw.builder import Builder
from ftw.builder import create
from ftw.testbrowser import browsing
from ftw.testbrowser.pages.statusmessages import assert_message
from opengever.testing import FunctionalTestCase


class TestRemoveConfirmationView(FunctionalTestCase):

    def setUp(self):
        super(TestRemoveConfirmationView, self).setUp()

        self.grant('Editor')
        self.dossier = create(Builder('dossier'))

        self.doc1 = create(Builder('document')
                           .within(self.dossier)
                           .trashed())
        self.doc2 = create(Builder('document')
                           .within(self.dossier)
                           .trashed())

    @browsing
    def test_redirects_to_trash_tab_when_no_documents_selected(self, browser):
        browser.login().open(self.dossier, view='remove_confirmation')

        self.assertEquals('{}#trash'.format(self.dossier.absolute_url()),
                          browser.url)
        assert_message('You have not selected any items')
