from ftw.builder import Builder
from ftw.builder import create
from ftw.testbrowser import browsing
from opengever.core.testing import activate_filing_number
from opengever.core.testing import inactivate_filing_number
from opengever.testing import FunctionalTestCase
import urllib


class TestSearchForm(FunctionalTestCase):

    use_browser = True

    def test_filing_number_fields_is_hidden_in_site_without_filing_number_support(self):
        self.browser.open('http://nohost/plone/advanced_search')

        with self.assertRaises(LookupError):
            self.browser.fill({'Filing number': 'Test'})


class TestSearchFormWithFilingNumberSupport(FunctionalTestCase):

    def setUp(self):
        super(TestSearchFormWithFilingNumberSupport, self).setUp()
        activate_filing_number(self.portal)

    def tearDown(self):
        super(TestSearchFormWithFilingNumberSupport, self).tearDown()
        inactivate_filing_number(self.portal)

    @browsing
    def test_filing_number_field_is_displayed_in_a_filing_number_supported_site(self, browser):
        browser.login().open(view='advanced_search')
        browser.fill({'Filing number': 'Test'})


class TestSearchFormObjectProvidesDescription(FunctionalTestCase):
    use_browser = True

    def test_contains_special_info_in_a_multi_client_setup(self):
        create(Builder('admin_unit'))

        self.browser.open('%s/advanced_search' % self.portal.absolute_url())

        formhelp = self.browser.css(
            '#formfield-form-widgets-object_provides span.formHelp')[0]
        self.assertEquals(
            'Select the contenttype to be searched for.'
            'It searches only items from the current client.',
            formhelp.plain_text())

    def test_not_contains_client_info_in_a_single_client_setup(self):
        self.browser.open('%s/advanced_search' % self.portal.absolute_url())

        formhelp = self.browser.css(
            '#formfield-form-widgets-object_provides span.formHelp')[0]
        self.assertEquals(
            'Select the contenttype to be searched for.',
            formhelp.plain_text())


class TestSearchWithContent(FunctionalTestCase):
    use_browser = True

    def setUp(self):
        super(TestSearchWithContent, self).setUp()

        self.dossier1 = create(Builder("dossier").titled(u"Dossier1"))
        self.dossier2 = create(Builder("dossier").titled(u"Dossier2"))

    def test_search_dossiers(self):
        self.browser.open('%s/advanced_search' % self.dossier1.absolute_url())
        self.browser.fill({'form.widgets.searchableText': "dossier1",
                           'form.widgets.object_provides:list': ['opengever.dossier.behaviors.dossier.IDossierMarker']})
        self.browser.click('form.buttons.button_search')
        self.assertSearchResultCount(1)

        self.browser.open('http://nohost/plone/@@search?object_provides=opengever.dossier.behaviors.dossier.IDossierMarker&SearchableText=dossier1')

    def test_search_documents(self):
        create(Builder("document").within(self.dossier1).titled("Document1"))
        create(Builder("document").within(self.dossier2).titled("Document2"))

        # search documents (we can't find the document because we must change the content-type)
        self.browser.open('%s/advanced_search' % self.dossier1.absolute_url())
        self.browser.fill({'form.widgets.searchableText': "document1",
                           'form.widgets.object_provides:list': ['opengever.dossier.behaviors.dossier.IDossierMarker']})
        self.browser.click('form.buttons.button_search')
        self.assertSearchResultCount(0)
        self.browser.open('http://nohost/plone/@@search?object_provides=opengever.dossier.behaviors.dossier.IDossierMarker&SearchableText=document1')

        # search documents with the right content-type
        self.browser.open('%s/advanced_search' % self.dossier1.absolute_url())
        self.browser.fill({'form.widgets.searchableText': "(document1)",
                          'form.widgets.object_provides:list': ['opengever.document.behaviors.IBaseDocument']})
        self.browser.click('form.buttons.button_search')
        self.browser.open('http://nohost/plone/@@search?object_provides=opengever.document.behaviors.IBaseDocument&SearchableText=document1')
        self.assertSearchResultCount(1)

    def test_search_tasks(self):
        create(Builder("task").within(self.dossier1).titled("Task1"))
        create(Builder("task").within(self.dossier2).titled("Task2"))

        # search tasks (we can't find the task because we must change the content-type)
        self.browser.open('%s/advanced_search' % self.dossier1.absolute_url())
        self.browser.fill({'form.widgets.searchableText': "task1",
                           'form.widgets.object_provides:list': ['opengever.document.behaviors.IBaseDocument']})
        self.browser.click('form.buttons.button_search')
        self.assertSearchResultCount(0)
        self.browser.open('http://nohost/plone/@@search?object_provides=opengever.document.behaviors.IBaseDocument&SearchableText=task1')


        # search tasks with the right content-type
        self.browser.open('%s/advanced_search' % self.dossier1.absolute_url())
        self.browser.fill({'form.widgets.searchableText': "task1",
                          'form.widgets.object_provides:list': ['opengever.task.task.ITask']})
        self.browser.click('form.buttons.button_search')
        self.assertSearchResultCount(1)
        self.browser.open('http://nohost/plone/@@search?object_provides=opengever.task.task.ITask&SearchableText=task1')

    def assertSearchResultCount(self, count):
        self.assertEquals(str(count), self.browser.locate("#search-results-number").text)


class TestSearchWithoutContent(FunctionalTestCase):

    def setUp(self):
        super(TestSearchWithoutContent, self).setUp()

        activate_filing_number(self.portal)

        self.dossier1 = create(Builder("dossier"))

    def tearDown(self):
        super(TestSearchWithoutContent, self).tearDown()

        inactivate_filing_number(self.portal)

    def assertBrowserUrlContainsSearchParams(self, browser, params):
        url = "http://nohost/plone/@@search?{}".format(urllib.urlencode(params))
        self.assertEqual(browser.url, url)

    @browsing
    def test_date_min_or_max_range_is_queried(self, browser):
        browser.login()
        browser.open(view='advanced_search')
        browser.fill({'form.widgets.object_provides:list': 'opengever.dossier.behaviors.dossier.IDossierMarker',
                      'form.widgets.start_1': "1/1/10",
                      'form.widgets.end_2': "4/1/10"})
        browser.css('#form-buttons-button_search').first.click()

        self.assertBrowserUrlContainsSearchParams(browser, [
            ('object_provides', 'opengever.dossier.behaviors.dossier.IDossierMarker'),
            ('start_usage', 'min'),
            ('start:list', '01/01/10'),
            ('end_usage', 'max'),
            ('end:list', '04/02/10'),
        ])

    @browsing
    def test_validate_searchstring_for_dossiers(self, browser):
        browser.open(view='advanced_search')
        browser.fill({'form.widgets.searchableText': "dossier1",
                      'form.widgets.object_provides:list': ['opengever.dossier.behaviors.dossier.IDossierMarker'],
                      'form.widgets.start_1': "1/1/10",
                      'form.widgets.start_2': "2/1/10",
                      'form.widgets.end_1': "3/1/10",
                      'form.widgets.end_2': "4/1/10",
                      'form.widgets.reference': "OG 14.2",
                      'form.widgets.sequence_number': "5",
                      'form.widgets.searchable_filing_no': "14",
                      'form.widgets.dossier_review_state:list': 'dossier-state-active'})
        browser.css('#form-buttons-button_search').first.click()

        self.assertBrowserUrlContainsSearchParams(browser, [
            ('object_provides', 'opengever.dossier.behaviors.dossier.IDossierMarker'),
            ('SearchableText', 'dossier1'),
            ('start_usage', 'minmax'),
            ('start:list', '01/01/10'),
            ('start:list', '02/02/10'),
            ('end_usage', 'minmax'),
            ('end:list', '03/01/10'),
            ('end:list', '04/02/10'),
            ('reference', 'OG%2014.2'),
            ('sequence_number:int', '5'),
            ('searchable_filing_no', '14'),
            ('review_state:list', 'dossier-state-active'),
        ])

    @browsing
    def test_validate_searchstring_for_documents(self, browser):
        browser.open(view='advanced_search')
        browser.fill({'form.widgets.searchableText': "document1",
                      'form.widgets.object_provides:list': 'opengever.document.behaviors.IBaseDocument',
                      'form.widgets.receipt_date_1': "1/1/10",
                      'form.widgets.receipt_date_2': "2/1/10",
                      'form.widgets.delivery_date_1': "3/1/10",
                      'form.widgets.delivery_date_2': "4/1/10",
                      'form.widgets.document_author': "Eduard",
                      'form.widgets.sequence_number': "5",
                      'form.widgets.trashed:list': True})
        browser.css('#form-buttons-button_search').first.click()

        self.assertBrowserUrlContainsSearchParams(browser, [
            ('object_provides', 'opengever.document.behaviors.IBaseDocument'),
            ('SearchableText', 'document1'),
            ('receipt_date_usage', 'minmax'),
            ('receipt_date:list', '01/01/10'),
            ('receipt_date:list', '02/02/10'),
            ('delivery_date_usage', 'minmax'),
            ('delivery_date:list', '03/01/10'),
            ('delivery_date:list', '04/02/10'),
            ('document_author', 'Eduard'),
            ('trashed:list:boolean', 'True'),
            ('trashed:list:boolean', 'False'),
        ])

    @browsing
    def test_validate_searchstring_for_tasks(self, browser):
        browser.open(view='advanced_search')
        browser.fill({'form.widgets.searchableText': "task1",
                      'form.widgets.object_provides:list': 'opengever.task.task.ITask',
                      'form.widgets.deadline_1': "1/1/10",
                      'form.widgets.deadline_2': "2/1/10",
                      'form.widgets.task_type:list': 'information',
                      'form.widgets.dossier_review_state:list': 'dossier-state-active'})
        browser.css('#form-buttons-button_search').first.click()

        self.assertBrowserUrlContainsSearchParams(browser, [
            ('object_provides', 'opengever.task.task.ITask'),
            ('SearchableText', 'task1'),
            ('deadline_usage', 'minmax'),
            ('deadline:list', '01/01/10'),
            ('deadline:list', '02/02/10'),
            ('task_type', 'information'),
        ])

    @browsing
    def test_disable_unload_protection(self, browser):
        browser.open(view='advanced_search')
        self.assertNotIn('enableUnloadProtection', browser.contents)
