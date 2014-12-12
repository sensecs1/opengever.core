from ftw.builder import Builder
from ftw.builder import create
from ftw.testbrowser import browsing
from opengever.testing import FunctionalTestCase
from plone.app.testing import TEST_USER_ID


class TestNotificationViewlet(FunctionalTestCase):

    def setUp(self):
        super(TestNotificationViewlet, self).setUp()
        self.test_watcher = create(Builder('watcher').having(user_id=TEST_USER_ID))
        self.hugo = create(Builder('watcher').having(user_id='hugo'))

        self.resource_a = create(Builder('resource')
                                 .oguid('fd:123')
                                 .having(watchers=[self.hugo, self.test_watcher]))

        self.activity_a = create(Builder('activity')
                                 .having(resource=self.resource_a,
                                         summary='Task added'))
        self.activity_b = create(Builder('activity')
                                 .having(resource=self.resource_a,
                                         summary='Task accepted'))
        self.activity_c = create(Builder('activity')
                                 .having(resource=self.resource_a,
                                         summary='Task resolved'))

    @browsing
    def test_header_contains_number_of_unread_messages(self, browser):
        create(Builder('notification')
               .having(activity=self.activity_a,watcher=self.test_watcher))
        create(Builder('notification')
               .having(activity=self.activity_b,watcher=self.test_watcher))
        create(Builder('notification')
               .having(activity=self.activity_c,watcher=self.test_watcher))

        browser.login().open()
        self.assertEquals('3',
                          browser.css('#portal-notifications .num-unread').first.text)

    @browsing
    def test_number_of_unread_messages_is_not_display_when_its_0(self, browser):
        browser.login().open()
        self.assertEquals([], browser.css('#portal-notifications .num-unread'))

    @browsing
    def test_unread_notifications_are_marked_with_unread_class(self, browser):
        create(Builder('notification')
               .having(activity=self.activity_a,watcher=self.test_watcher))
        create(Builder('notification')
               .as_read()
               .having(activity=self.activity_b,watcher=self.test_watcher))
        create(Builder('notification')
               .having(activity=self.activity_c,watcher=self.test_watcher))

        browser.login().open()

        self.assertEquals(
            ['Task added', 'Task resolved'],
            browser.css('.item-content.unread .item-summary').text)

    @browsing
    def test_notifications_is_limited_to_five_latest(self, browser):
        for i in range(7):
            create(Builder('notification')
                   .having(activity=self.activity_a,watcher=self.test_watcher))

        browser.login().open()
        self.assertEquals(5, len(browser.css('.notification-item')))
