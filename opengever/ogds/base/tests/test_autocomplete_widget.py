from ftw.builder import Builder
from ftw.builder import create
from opengever.ogds.base.autocomplete_widget import AutocompleteFieldWidget
from opengever.task.task import ITask
from opengever.testing import FunctionalTestCase
from plone.app.testing import TEST_USER_ID


class TestAutoCompleteWidget(FunctionalTestCase):
    use_default_fixture = False

    def _init_widget(self):
        return AutocompleteFieldWidget(
            ITask['issuer'], self.portal.REQUEST)

    def setUp(self):
        super(TestAutoCompleteWidget, self).setUp()
        self.grant('Member', 'Manager')
        self.widget = self._init_widget()

        testuser = create(Builder('ogds_user')
                          .having(userid=TEST_USER_ID,
                                  firstname='Test',
                                  lastname='User'))

        hugo = create(Builder('ogds_user')
                      .having(userid='hugo.boss',
                              firstname='Hugo',
                              lastname='Boss'))

        franz = create(Builder('ogds_user')
                       .having(userid='franz.michel',
                               firstname='Franz',
                               lastname='Michel'))

        admin_unit = create(Builder('admin_unit')
                            .as_current_admin_unit())
        create(Builder('org_unit')
               .id(u'client1')
               .having(admin_unit=admin_unit)
               .as_current_org_unit()
               .assign_users([testuser, hugo, franz]))

    def test_new_term_for_unkown_user_is_added_to_hidden_terms_vocabylary(self):
        task = create(Builder('task').having(issuer='hans.peter'))
        self.widget.context = task
        source = self.widget.bound_source

        self.assertSequenceEqual(['hans.peter'], source.hidden_terms)

    def test_initally_no_hidden_terms_are_set(self):
        task = create(Builder('task'))

        self.widget.context = task
        source = self.widget.bound_source

        self.assertItemsEqual(
            [u'hugo.boss', u'franz.michel', TEST_USER_ID, u'inbox:client1'],
            [i.value for i in source])

        self.assertEquals([], source.hidden_terms)

    def test_not_existing_term_in_vocabulary_is_not_shown_in_listing(self):
        task = create(Builder('task').having(issuer='not.existing'))

        self.widget.context = task

        self.assertItemsEqual(
            [u'hugo.boss', u'franz.michel', TEST_USER_ID, u'inbox:client1'],
            [i.value for i in self.widget.bound_source])

    def test_not_existing_term_in_vocabulary_is_included_in_hidden_terms(self):
        task = create(Builder('task').having(issuer='not.existing'))

        self.widget.context = task
        self.assertEquals([u'not.existing'],
                          self.widget.bound_source.hidden_terms)
