from opengever.core.testing import OPENGEVER_FIXTURE
from plone.app.testing import IntegrationTesting, FunctionalTesting
from plone.app.testing import PloneSandboxLayer
from plone.app.testing import TEST_USER_ID
from plone.app.testing import setRoles


class ContactLayer(PloneSandboxLayer):
    defaultBases = (OPENGEVER_FIXTURE,)

    def setUpPloneSite(self, portal):
        setRoles(portal, TEST_USER_ID, ['Member', 'Contributor', 'Manager'])


CONTACT_FIXTURE = ContactLayer()
CONTACT_INTEGRATION_TESTING = IntegrationTesting(
    bases=(CONTACT_FIXTURE,), name="Contact:Integration")
CONTACT_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(CONTACT_FIXTURE,), name="Contact:Functional")
