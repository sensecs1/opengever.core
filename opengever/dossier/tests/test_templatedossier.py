from datetime import date
from datetime import datetime
from ftw.builder import Builder
from ftw.builder import create
from ftw.testbrowser import browsing
from ftw.testbrowser.pages import factoriesmenu
from ftw.testbrowser.pages import plone
from ooxml_docprops import read_properties
from opengever.dossier.docprops import TemporaryDocFile
from opengever.dossier.interfaces import ITemplateDossierProperties
from opengever.dossier.templatedossier.interfaces import ITemplateUtility
from opengever.journal.handlers import DOC_PROPERTIES_UPDATED
from opengever.journal.tests.utils import get_journal_entry
from opengever.testing import FunctionalTestCase
from opengever.testing.pages import sharing_tab_data
from plone.app.testing import TEST_USER_ID
from plone.registry.interfaces import IRegistry
from zope.component import getUtility
import transaction


class TestDocumentWithTemplateForm(FunctionalTestCase):

    use_browser = True

    expected_doc_properties = [
        ('User.ID', TEST_USER_ID,),
        ('User.FullName', 'Peter',),
        ('Dossier.ReferenceNumber', 'Client1 / 2'),
        ('Dossier.Title', 'My Dossier'),
        ('Document.ReferenceNumber', 'Client1 / 2 / 4'),
        ('Document.SequenceNumber', '4'),
    ]

    def setUp(self):
        super(TestDocumentWithTemplateForm, self).setUp()
        self.grant('Manager')
        self.setup_fullname(fullname='Peter')

        registry = getUtility(IRegistry)
        self.props = registry.forInterface(ITemplateDossierProperties)
        self.props.create_doc_properties = True

        self.modification_date = datetime(2012, 12, 28)

        self.templatedossier = create(Builder('templatedossier'))
        self.template_a = create(Builder('document')
                                 .titled('Template A')
                                 .within(self.templatedossier)
                                 .with_modification_date(self.modification_date))
        self.template_b = create(Builder('document')
                                 .titled('Template B')
                                 .within(self.templatedossier)
                                 .with_dummy_content()
                                 .with_modification_date(self.modification_date))
        self.dossier = create(Builder('dossier').titled(u'My Dossier'))

        self.template_b_path = '/'.join(self.template_b.getPhysicalPath())

    def assert_doc_properties_updated_journal_entry_generated(self, document):
        entry = get_journal_entry(document)

        self.assertEqual(DOC_PROPERTIES_UPDATED, entry['action']['type'])
        self.assertEqual(TEST_USER_ID, entry['actor'])
        self.assertEqual('', entry['comments'])

    @browsing
    def test_form_list_all_templates(self, browser):
        browser.login().open(self.dossier, view='document_with_template')
        self.assertEquals(
            [{'': '',
              'Creator': 'test_user_1_',
              'Modified': '28.12.2012',
              'title': 'Template A'},

             {'': '',
              'Creator': 'test_user_1_',
              'Modified': '28.12.2012',
              'title': 'Template B'}],
            browser.css('table.listing').first.dicts())

    @browsing
    def test_template_list_includes_nested_templates(self, browser):

        subtemplatedossier = create(Builder('templatedossier')
                                    .within(self.templatedossier))
        create(Builder('document')
               .titled('Template C')
               .within(subtemplatedossier)
               .with_modification_date(self.modification_date))

        browser.login().open(self.dossier, view='document_with_template')

        self.assertEquals(
            [{'': '',
              'Creator': 'test_user_1_',
              'Modified': '28.12.2012',
              'title': 'Template A'},
             {'': '',
              'Creator': 'test_user_1_',
              'Modified': '28.12.2012',
              'title': 'Template B'},
             {'': '',
              'Creator': 'test_user_1_',
              'Modified': '28.12.2012',
              'title': 'Template C'}],

            browser.css('table.listing').first.dicts())

    @browsing
    def test_template_titles_are_linked(self, browser):
        browser.login().open(self.dossier, view='document_with_template')
        browser.find('Template B').click()
        self.assertEquals(self.template_b, browser.context)

    @browsing
    def test_cancel_redirects_to_the_dossier(self, browser):
        browser.login().open(self.dossier, view='document_with_template')
        browser.find('Cancel').click()
        self.assertEquals(self.dossier, browser.context)
        self.assertEquals('tabbed_view', plone.view())

    @browsing
    def test_save_redirects_to_the_dossiers_document_tab(self, browser):
        browser.login().open(self.dossier, view='document_with_template')
        browser.fill({'paths:list': self.template_b_path,
                      'title': 'Test Document',
                      'Edit after creation':False}).save()

        self.assertEquals(self.dossier, browser.context)
        self.assertEquals(self.dossier.absolute_url() + '#documents',
                          browser.url)

    @browsing
    def test_new_document_is_titled_with_the_form_value(self, browser):
        browser.login().open(self.dossier, view='document_with_template')
        browser.fill({'paths:list': self.template_b_path,
                      'title': 'Test Document'}).save()

        document = self.dossier.listFolderContents()[0]

        self.assertEquals('Test Document', document.title)

    @browsing
    def test_new_document_values_are_filled_with_default_values(self, browser):
        browser.login().open(self.dossier, view='document_with_template')
        browser.fill({'paths:list': self.template_b_path,
                      'title': 'Test Document'}).save()

        document = self.dossier.listFolderContents()[0]
        self.assertEquals(date.today(), document.document_date)
        self.assertEquals(u'privacy_layer_no', document.privacy_layer)

    @browsing
    def test_file_of_the_new_document_is_a_copy_of_the_template(self, browser):
        browser.login().open(self.dossier, view='document_with_template')
        browser.fill({'paths:list': self.template_b_path,
                      'title': 'Test Document'}).save()

        document = self.dossier.listFolderContents()[0]

        self.assertEquals(self.template_b.file.data, document.file.data)
        self.assertNotEquals(self.template_b.file, document.file)

    @browsing
    def test_properties_are_added_when_created_from_template_with_doc_properties(self, browser):
        template_word = create(Builder('document')
                               .titled('Word Docx template')
                               .within(self.templatedossier)
                               .with_asset_file('with_custom_properties.docx'))
        template_path = '/'.join(template_word.getPhysicalPath())

        browser.login().open(self.dossier, view='document_with_template')
        browser.fill({'paths:list': template_path,
                      'title': 'Test Docx'}).save()

        document = self.dossier.listFolderContents()[0]
        self.assertEquals(u'test-docx.docx', document.file.filename)
        with TemporaryDocFile(document.file) as tmpfile:
            properties = read_properties(tmpfile.path)
            self.assertItemsEqual(
                self.expected_doc_properties + [('Test', 'Peter')],
                properties)
        self.assert_doc_properties_updated_journal_entry_generated(document)

    @browsing
    def test_properties_are_added_when_created_from_template_without_doc_properties(self, browser):
        template_word = create(Builder('document')
                               .titled('Word Docx template')
                               .within(self.templatedossier)
                               .with_asset_file('without_custom_properties.docx'))
        template_path = '/'.join(template_word.getPhysicalPath())

        browser.login().open(self.dossier, view='document_with_template')
        browser.fill({'paths:list': template_path,
                      'title': 'Test Docx'}).save()

        document = self.dossier.listFolderContents()[0]
        self.assertEquals(u'test-docx.docx', document.file.filename)
        with TemporaryDocFile(document.file) as tmpfile:
            properties = read_properties(tmpfile.path)
            self.assertItemsEqual(self.expected_doc_properties, properties)
        self.assert_doc_properties_updated_journal_entry_generated(document)

    @browsing
    def test_doc_properties_are_not_created_when_disabled(self, browser):
        self.props.create_doc_properties = False
        template_word = create(Builder('document')
                               .titled('Word Docx template')
                               .within(self.templatedossier)
                               .with_asset_file('without_custom_properties.docx'))
        template_path = '/'.join(template_word.getPhysicalPath())

        browser.login().open(self.dossier, view='document_with_template')
        browser.fill({'paths:list': template_path,
                      'title': 'Test Docx'}).save()

        document = self.dossier.listFolderContents()[0]
        self.assertEquals(u'test-docx.docx', document.file.filename)
        with TemporaryDocFile(document.file) as tmpfile:
            self.assertItemsEqual([], read_properties(tmpfile.path))


class TestTemplateDossier(FunctionalTestCase):

    def setUp(self):
        super(TestTemplateDossier, self).setUp()
        self.grant('Manager')

    @browsing
    def test_adding(self, browser):
        browser.login().open(self.portal)
        factoriesmenu.add('Template Dossier')
        browser.fill({'Title': 'Templates',
                      'Responsible': TEST_USER_ID}).save()

        self.assertEquals('tabbed_view', plone.view())

    @browsing
    def test_addable_types(self, browser):
        templatedossier = create(Builder('templatedossier'))
        browser.login().open(templatedossier)

        self.assertEquals(
            ['Document', 'TaskTemplateFolder', 'Template Dossier'],
            factoriesmenu.addable_types())


class TestTemplateFolderUtility(FunctionalTestCase):

    def setUp(self):
        super(TestTemplateFolderUtility, self).setUp()
        self.utility = getUtility(ITemplateUtility, 'opengever.templatedossier')
        self.grant('Manager')

    def test_get_template_folder_returns_path_of_the_templatedossier(self):
        templatedossier = create(Builder('templatedossier'))

        self.assertEquals(
            '/'.join(templatedossier.getPhysicalPath()),
            self.utility.templateFolder(self.portal))

    def test_get_template_folder_returns_allways_root_templatefolder(self):
        templatedossier = create(Builder('templatedossier'))
        create(Builder('templatedossier')
               .within(templatedossier))

        self.assertEquals(
            '/'.join(templatedossier.getPhysicalPath()),
            self.utility.templateFolder(self.portal))


OVERVIEW_TAB = 'tabbedview_view-overview'
DOCUMENT_TAB = 'tabbedview_view-documents'
TRASH_TAB = 'tabbedview_view-trash'
JOURNAL_TAB = 'tabbedview_view-journal'
INFO_TAB = 'tabbedview_view-sharing'


class TestTemplateDossierListings(FunctionalTestCase):

    def setUp(self):
        super(TestTemplateDossierListings, self).setUp()
        self.grant('Manager')

        self.templatedossier = create(Builder('templatedossier'))
        self.dossier = create(Builder('dossier'))

    def test_receipt_delivery_and_subdossier_column_are_hidden_in_document_tab(self):
        view = self.templatedossier.unrestrictedTraverse(DOCUMENT_TAB)
        view.update()
        columns = [col.get('column') for col in view.columns]

        self.assertEquals(
            ['', 'sequence_number', 'Title', 'document_author',
             'document_date', 'checked_out', 'public_trial'],
            columns)

    def test_receipt_delivery_and_subdossier_column_are_hidden_in_trash_tab(self):
        view = self.templatedossier.unrestrictedTraverse(TRASH_TAB)
        view.update()
        columns = [col.get('column') for col in view.columns]

        self.assertEquals(
            ['', 'sequence_number', 'Title',
             'document_author', 'document_date', 'public_trial'],
            columns)

    def test_enabled_actions_are_limited_in_document_tab(self):
        view = self.templatedossier.unrestrictedTraverse(DOCUMENT_TAB)
        self.assertEquals(['checkin_with_comment',
                           'checkin_without_comment',
                           'submit_additional_documents',
                           'trashed',
                           'copy_items',
                           'zip_selected'],
                          view.enabled_actions)

    def test_document_tab_lists_only_documents_directly_beneath(self):
        subdossier = create(Builder('templatedossier')
                            .within(self.templatedossier))
        document_a = create(Builder('document').within(self.templatedossier))
        create(Builder('document').within(subdossier))

        view = self.templatedossier.unrestrictedTraverse(DOCUMENT_TAB)
        view.update()

        self.assertEquals([document_a],
                          [brain.getObject() for brain in view.contents])

    def test_trash_tab_lists_only_documents_directly_beneath(self):
        subdossier = create(Builder('templatedossier')
                            .within(self.templatedossier))
        document_a = create(Builder('document')
                            .trashed()
                            .within(self.templatedossier))
        create(Builder('document').trashed().within(subdossier))

        view = self.templatedossier.unrestrictedTraverse(TRASH_TAB)
        view.update()

        self.assertEquals([document_a],
                          [brain.getObject() for brain in view.contents])


class TestTemplateDocumentTabs(FunctionalTestCase):

    def setUp(self):
        super(TestTemplateDocumentTabs, self).setUp()

        self.templatedossier = create(Builder('templatedossier'))
        self.template = create(Builder('document')
                               .within(self.templatedossier)
                               .titled('My Document'))
        self.grant('Manager')

    @browsing
    def test_template_overview_tab(self, browser):
        browser.login().open(self.template, view=OVERVIEW_TAB)
        table = browser.css('table.listing').first
        self.assertIn(['Title', 'My Document'], table.lists())

    def test_template_journal_tab(self):
        view = self.template.unrestrictedTraverse(JOURNAL_TAB)
        view.update()
        entry = view.contents[0]
        self.assertDictContainsSubset({'type': 'Document added'},
                                      entry['action'])
        self.assertEquals(TEST_USER_ID, entry['actor'])

    @browsing
    def test_template_info_tab(self, browser):
        browser.login()

        browser.open(self.template, view=INFO_TAB)
        self.assertEquals([['Logged-in users', False, False, False]],
                          sharing_tab_data())

        self.template.manage_setLocalRoles(TEST_USER_ID,
                                           ["Reader", "Contributor", "Editor"])
        transaction.commit()

        browser.open(self.template, view=INFO_TAB)
        self.assertEquals([['Logged-in users', False, False, False],
                           [TEST_USER_ID, True, True, True]],
                          sharing_tab_data())
