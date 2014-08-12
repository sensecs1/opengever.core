from Products.CMFCore.utils import getToolByName
from ftw.builder import Builder
from ftw.builder import create
from opengever.ogds.base.interfaces import IContactInformation
from opengever.ogds.base.utils import get_client_id
from opengever.testing import FunctionalTestCase
from opengever.testing import create_and_select_current_org_unit
from opengever.testing import create_client
from opengever.testing import create_ogds_user
from opengever.testing import obj2brain
from opengever.testing import select_current_org_unit
from plone.app.testing import TEST_USER_ID
from zope.component import getUtility


class TestClientUtils(FunctionalTestCase):

    def setUp(self):
        super(TestClientUtils, self).setUp()
        self.test_ou = create_and_select_current_org_unit('test_client')

    def test_get_client_id_returns_current_client_id(self):
        self.assertEquals(u'test_client', get_client_id())


class TestClientHelpers(FunctionalTestCase):

    def setUp(self):
        super(TestClientHelpers, self).setUp()
        self.info = getUtility(IContactInformation)

        self.client1 = create_client(clientid='client1')
        self.client2 = create_client(clientid='client2')
        create_client(clientid='client3', enabled=False)

        create_ogds_user(TEST_USER_ID, assigned_client=[self.client1],
                 firstname="Test", lastname="User")
        select_current_org_unit('client1')

    def test_get_clients_returns_all_enabled_clients(self):
        self.assertEquals([self.client1, self.client2], self.info.get_clients())

    def test_get_client_by_id_for_exsiting_client_returns_client(self):
        self.assertEquals(self.client1, self.info.get_client_by_id('client1'))

    def test_get_client_by_id_for_disabled_client_returns_none(self):
        self.assertEquals(None, self.info.get_client_by_id('unknown client'))

    def test_get_client_by_id_for_not_existing_client_returns_none(self):
        self.assertEquals(None, self.info.get_client_by_id('unknown client'))

    def test_user_is_assigned_to_client_if_he_is_in_the_client_users_group(self):
        create_ogds_user('hugo.boss', groups=('client1_users', ))

        self.assertFalse(
            self.info.is_client_assigned(userid='hugo.boss', client_id='client2'))
        self.assertTrue(
            self.info.is_client_assigned(userid='hugo.boss', client_id='client1'))

    def test_get_assigned_clients_returns_all_clients_wich_the_users_is_in_the_clients_usergroup(self):
        create_ogds_user('hugo.boss', groups=('client1_users', ))
        create_ogds_user('jamie.lannister', groups=('client1_users', 'client2_users'))

        self.assertEquals(
            [self.client1, ],
            self.info.get_assigned_clients(userid='hugo.boss'))

        self.assertEquals(
            [self.client1, self.client2],
            self.info.get_assigned_clients(userid='jamie.lannister'))


class TestOneClientSetupHelper(FunctionalTestCase):

    def setUp(self):
        super(TestOneClientSetupHelper, self).setUp()
        self.info = getUtility(IContactInformation)

    def test_is_one_client_setup(self):
        create_and_select_current_org_unit('client')

        self.assertTrue(self.info.is_one_client_setup())

    def test_a_setup_with_multiple_clients_is_not_a_one_client_setup(self):
        create_and_select_current_org_unit('client')
        create_client(clientid='client2')

        self.assertFalse(self.info.is_one_client_setup())


class TestUserHelpers(FunctionalTestCase):

    def setUp(self):
        super(TestUserHelpers, self).setUp()
        self.info = getUtility(IContactInformation)

    def test_getting_profile_url_returns_user_detail_view_url(self):
        create_ogds_user('hugo.boss')

        self.assertEquals(
            u'http://nohost/plone/@@user-details/hugo.boss',
            self.info.get_profile_url('hugo.boss'))


class TestGroupHelpers(FunctionalTestCase):

    def setUp(self):
        super(TestGroupHelpers, self).setUp()
        self.info = getUtility(IContactInformation)

        self.client1 = create_client(clientid='client1')
        self.client2 = create_client(clientid='client2')
        create_ogds_user(TEST_USER_ID, assigned_client=[self.client1],
                         firstname="Test", lastname="User")
        select_current_org_unit('client1')

    def test_list_users_group_returns_a_list_of_all_group_ids_the_user_is_assigned(self):
        create_ogds_user('hugo.boss', groups=('client1_users', 'client1_inbox_users'))

        self.assertEquals(
            ['client1_users', 'client1_inbox_users'],
            [group.groupid for group in self.info.list_user_groups('hugo.boss')])

    def test_user_is_inbox_group_when_he_is_in_the_inbox_group_of_the_given_client(self):
        create_ogds_user('hugo.boss', groups=('client1_inbox_users', ))
        create_ogds_user('jamie.lannister',
                         groups=('client1_inbox_users', 'client2_inbox_users'))

        create_client(clientid='client1', inbox_group='client1_inbox_users')
        create_client(clientid='client2', inbox_group='client2_inbox_users')

        self.assertTrue(self.info.is_user_in_inbox_group(
            userid='hugo.boss', client_id='client1'))
        self.assertFalse(self.info.is_user_in_inbox_group(
            userid='hugo.boss', client_id='client2'))

        self.assertTrue(self.info.is_user_in_inbox_group(
            userid='jamie.lannister', client_id='client1'))
        self.assertTrue(self.info.is_user_in_inbox_group(
            userid='jamie.lannister', client_id='client2'))

    def test_get_group_of_inbox_returns_group(self):
        create_client(clientid='client1', inbox_group='client1_inbox_users')

        self.assertEquals('client1_inbox_users',
                          self.info.get_groupid_of_inbox("inbox:client1"))


class TestContactInfoAdditionals(FunctionalTestCase):

    def setUp(self):
        super(TestContactInfoAdditionals, self).setUp()
        self.info = getUtility(IContactInformation)

    def test_contacts_or_inboxes_is_not_a_user(self):
        self.assertFalse(self.info.is_user(u'inbox:client1'))
        self.assertFalse(self.info.is_user(u'contact:croft-lara'))

    def test_all_possibly_valid_userids_are_a_user(self):
        self.assertTrue(self.info.is_user('hugo.boss'))
        self.assertTrue(self.info.is_user('peter.muster'))

    def test_only_prinicpal_prefixed_with_contact_and_colon_is_contact(self):
        self.assertTrue(self.info.is_contact('contact:croft-lara'))
        self.assertFalse(self.info.is_contact('croft-lara'))
        self.assertFalse(self.info.is_contact('inbox:client1'))

    def test_only_prinicpal_prefixed_with_inbox_and_colon_is_a_inbox(self):
        self.assertTrue(self.info.is_inbox('inbox:client1'))
        self.assertFalse(self.info.is_inbox('contact:croft-lara'))
        self.assertFalse(self.info.is_inbox('hugo.boss'))

    def test_list_contacts_return_all_contact_brains(self):
        create(Builder('contact')
               .having(**{'firstname': u'Lara',
                          'lastname': u'Croft',
                          'email': u'lara.croft@test.ch'}))
        create(Builder('contact')
               .having(**{'firstname': u'Super',
                          'lastname': u'M\xe4n',
                          'email': 'superman@test.ch'}))
        create(Builder('contact')
               .having(**{'firstname': u'James',
                          'lastname': u'Bond',
                          'email': None}))

        self.assertEquals(
            ['croft-lara', 'man-super', 'bond-james'],
            [brain.getId for brain in self.info.list_contacts()])

        self.assertEquals(
            ['contact:croft-lara',
             'contact:man-super',
             'contact:bond-james'],
            [contact.contactid for contact in self.info.list_contacts()])
