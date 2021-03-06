from ftw.builder import Builder
from ftw.builder import create
from opengever.base.interfaces import IReferenceNumberSettings
from opengever.repository.behaviors.referenceprefix import IReferenceNumberPrefix
from opengever.repository.repositoryfolder import IRepositoryFolderSchema
from opengever.testing import FunctionalTestCase
from plone.dexterity.interfaces import IDexterityFTI
from plone.registry.interfaces import IRegistry
from zope.component import createObject
from zope.component import getUtility
from zope.component import queryUtility


class TestRepositoryFolder(FunctionalTestCase):

    def test_adding(self):
        self.grant('Reviewer', 'Manager')
        self.portal.invokeFactory('opengever.repository.repositoryfolder', 'repository1')
        r1 = self.portal['repository1']
        self.failUnless(IRepositoryFolderSchema.providedBy(r1))

    def test_fti(self):
        fti = queryUtility(IDexterityFTI, name='opengever.repository.repositoryfolder')
        self.assertNotEquals(None, fti)

    def test_schema(self):
        fti = queryUtility(IDexterityFTI, name='opengever.repository.repositoryfolder')
        schema = fti.lookupSchema()
        self.assertEquals(IRepositoryFolderSchema, schema)

    def test_factory(self):
        fti = queryUtility(IDexterityFTI, name='opengever.repository.repositoryfolder')
        factory = fti.factory
        new_object = createObject(factory)
        self.failUnless(IRepositoryFolderSchema.providedBy(new_object))


class TestRepositoryFolderTitleAccessor(FunctionalTestCase):

    def setUp(self):
        super(TestRepositoryFolderTitleAccessor, self).setUp()

        repository_1 = create(Builder('repository'))

        repository_1_1 = create(Builder('repository')
                                .within(repository_1))

        self.repository_folder = create(Builder('repository')
                                  .within(repository_1_1)
                                  .titled(u'Repositoryfolder XY'))

    def test_returns_reference_number_and_title_seperatoded_with_space(self):
        self.assertEquals(
            '1.1.1. Repositoryfolder XY',
            self.repository_folder.Title())

    def test_Title_accessor_use_reference_formatters_seperator(self):
        registry = getUtility(IRegistry)
        proxy = registry.forInterface(IReferenceNumberSettings)
        proxy.formatter = 'grouped_by_three'

        self.assertEquals(
            '111 Repositoryfolder XY',
            self.repository_folder.Title())


class TestRepositoryFolderWithBrowser(FunctionalTestCase):
    use_browser = True

    def setUp(self):
        super(TestRepositoryFolderWithBrowser, self).setUp()
        self.grant('Manager')

        # Since the Generic Setup profile was imported,
        # we should have a some FTIs registered::
        pt = self.portal.portal_types
        pt.get('opengever.repository.repositoryfolder', None)
        pt.get('opengever.repository.repositoryroot', None)

    def test_repository_folder(self):
        # So, lets create the repository-root::
        self.browser.open('http://nohost/plone/folder_factories')
        self.assertPageContains('opengever.repository.repositoryroot')
        self.browser.getControl('RepositoryRoot').click()
        self.browser.getControl('Add').click()
        self.browser.getControl('Title').value = 'Registraturplan'
        self.browser.getControl('Description').value = ''
        self.browser.getControl('Save').click()
        self.browser.assert_url('http://nohost/plone/registraturplan/tabbed_view')

        # Now, create our first repository folder::
        self.browser.open('./folder_factories')
        self.assertPageContains('opengever.repository.repositoryfolder')
        self.browser.getControl('RepositoryFolder').click()
        self.browser.getControl('Add').click()
        self.browser.getControl('Title').value = 'Accounting'
        self.browser.getControl('Save').click()
        self.browser.assert_url('http://nohost/plone/registraturplan/accounting/tabbed_view')

        # Check some stuff::
        obj = self.portal.get('registraturplan').get('accounting')
        self.assertEquals(u'1', IReferenceNumberPrefix(obj).reference_number_prefix)
        self.assertEquals(('test_user_1_',), obj.listCreators())

        # Add another one::
        self.browser.open('http://nohost/plone/registraturplan/++add++opengever.repository.repositoryfolder')
        self.browser.getControl('Title').value = 'Custody'
        self.browser.getControl('Save').click()
        self.browser.assert_url('http://nohost/plone/registraturplan/custody/tabbed_view')

        obj = self.portal.get('registraturplan').get('custody')
        self.assertEquals(u'2', IReferenceNumberPrefix(obj).reference_number_prefix)
