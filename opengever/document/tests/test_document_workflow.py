from ftw.builder import Builder
from ftw.builder import create
from opengever.testing import FunctionalTestCase
from plone import api
from plone.api.exc import InvalidParameterError


class TestDocumentWorkflow(FunctionalTestCase):

    def test_document_draft_state_is_initial_state(self):
        doc = create(Builder('document'))

        self.assertEquals('document-state-draft',
                          api.content.get_state(obj=doc))

    def test_document_can_only_be_removed_with_remove_gever_content_permission(self):
        doc = create(Builder('document'))

        self.grant('Editor')
        api.content.transition(obj=doc,
                               transition='document-transition-remove')

        self.assertEquals('document-state-removed',
                          api.content.get_state(obj=doc))

    def test_document_can_only_be_restored_with_manage_portal_permission(self):

        doc = create(Builder('document').in_state('document-state-removed'))

        with self.assertRaises(InvalidParameterError):
            api.content.transition(obj=doc, transition='document-transition-restore')

        self.grant('Manager')
        api.content.transition(obj=doc,
                               transition='document-transition-restore')

        self.assertEquals('document-state-draft',
                          api.content.get_state(obj=doc))
