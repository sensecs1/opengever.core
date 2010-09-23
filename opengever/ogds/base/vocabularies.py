from five import grok
from opengever.ogds.base.interfaces import IClientCommunicator
from opengever.ogds.base.interfaces import IContactInformation
from opengever.ogds.base.utils import get_current_client
from opengever.ogds.base.vocabulary import ContactsVocabulary
from zope.component import getUtility
from zope.globalrequest import getRequest
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleVocabulary


class UsersVocabularyFactory(grok.GlobalUtility):
    """ Vocabulary of all users with a valid login.
    """

    grok.provides(IVocabularyFactory)
    grok.name('opengever.ogds.base.UsersVocabulary')

    def __call__(self, context):
        return ContactsVocabulary.create_with_provider(self.key_value_provider)

    def key_value_provider(self):
        info = getUtility(IContactInformation)
        for user in info.list_users():
            yield (user.userid,
                   info.describe(user.userid))


class UsersAndInboxesVocabularyFactory(grok.GlobalUtility):
    """Vocabulary of all users and all inboxes of enabled clients.
    """

    grok.provides(IVocabularyFactory)
    grok.name('opengever.ogds.base.UsersAndInboxesVocabulary')

    def __call__(self, context):
        return ContactsVocabulary.create_with_provider(self.key_value_provider)

    def key_value_provider(self):
        info = getUtility(IContactInformation)
        # all users
        for user in info.list_users():
            yield (user.userid,
                   info.describe(user.userid))
        # all inboxes
        for key, label in info.list_inboxes():
            yield (key, label)


class AssignedUsersVocabularyFactory(grok.GlobalUtility):
    """Vocabulary of all users assigned to the current client.
    """

    grok.provides(IVocabularyFactory)
    grok.name('opengever.ogds.base.AssignedUsersVocabulary')

    def __call__(self, context):
        return ContactsVocabulary.create_with_provider(self.key_value_provider)

    def key_value_provider(self):
        info = getUtility(IContactInformation)
        for user in info.list_assigned_users():
            yield (user.userid,
                   info.describe(user.userid))


class ContactsVocabularyFactory(grok.GlobalUtility):
    """Vocabulary of contacts.
    """

    grok.provides(IVocabularyFactory)
    grok.name('opengever.ogds.base.ContactsVocabulary')

    def __call__(self, context):
        return ContactsVocabulary.create_with_provider(self.key_value_provider)

    def key_value_provider(self):
        info = getUtility(IContactInformation)
        for contact in info.list_contacts():
            yield (contact.contactid,
                   info.describe(contact.contactid))


class ContactsAndUsersVocabularyFactory(grok.GlobalUtility):
    """Vocabulary of contacts and users.
    """

    grok.provides(IVocabularyFactory)
    grok.name('opengever.ogds.base.ContactsAndUsersVocabulary')

    def __call__(self, context):
        return ContactsVocabulary.create_with_provider(self.key_value_provider)

    def key_value_provider(self):
        info = getUtility(IContactInformation)
        # users
        for user in info.list_users():
            yield (user.userid,
                   info.describe(user.userid))
        for contact in info.list_contacts():
            yield (contact.contactid,
                   info.describe(contact.contactid))


class EmailContactsAndUsersVocabularyFactory(grok.GlobalUtility):
    """Vocabulary containing all users and contacts with each e-mail
    address they have.
    """

    grok.provides(IVocabularyFactory)
    grok.name('opengever.ogds.base.EmailContactsAndUsersVocabulary')

    def __call__(self, context):
        vocab = ContactsVocabulary.create_with_provider(
            self.key_value_provider)
        return vocab

    def key_value_provider(self):
        """yield the items

        key = mail-address
        value = Fullname [address], eg. Hugo Boss [hugo@boss.ch]
        """

        info = getUtility(IContactInformation)
        ids = [user.userid for user in info.list_users()]
        ids.extend([contact.contactid for contact
                    in info.list_contacts()])

        for userid in ids:
            yield(info.get_email(userid),
                  info.describe(userid, with_email=True))
            if info.get_email2(userid) != None:
                yield(info.get_email2(userid),
                      info.describe(userid, with_email2=True))


class AssignedClientsVocabularyFactory(grok.GlobalUtility):
    """Vocabulary of all assigned clients (=home clients) of the
    current user. The current client is not included!
    """

    grok.provides(IVocabularyFactory)
    grok.name('opengever.ogds.base.AssignedClientsVocabulary')


    def __call__(self, context):
        vocab = ContactsVocabulary.create_with_provider(
            self.key_value_provider)
        return vocab

    def key_value_provider(self):
        """yield the items

        key = mail-address
        value = Fullname [address], eg. Hugo Boss [hugo@boss.ch]
        """

        info = getUtility(IContactInformation)
        current_client_id = get_current_client().client_id

        for client in info.get_assigned_clients():
            if current_client_id != client.client_id:
                yield (client.client_id,
                       client.title)


class HomeDossiersVocabularyFactory(grok.GlobalUtility):
    """Vocabulary of all open dossiers on users home client.
    Key is the path of dossier relative to its plone site on the remote client.
    """

    grok.provides(IVocabularyFactory)
    grok.name('opengever.ogds.base.HomeDossiersVocabulary')

    def __call__(self, context):
        request = getRequest()
        terms = []

        info = getUtility(IContactInformation)
        comm = getUtility(IClientCommunicator)
        home_clients = info.get_assigned_clients()

        client_id = request.get(
            'client', request.get('form.widgets.client'))
        if type(client_id) in (list, tuple, set):
            client_id = client_id[0]
        client = info.get_client_by_id(client_id)

        if client not in home_clients:
            raise ValueError('Expected %s to be a ' % client_id + \
                                 'assigned client of the current user.')

        if client:
            for dossier in comm.get_open_dossiers(client.client_id):
                key = dossier['path']
                value = '%s: %s' % (dossier['reference_number'],
                                    dossier['title'])
                terms.append(SimpleVocabulary.createTerm(key,
                                                         key,
                                                         value))
        # XXX: remove sorting as soon as autocomplete widget is used
        terms.sort(lambda a,b:cmp(a.title, b.title))
        return SimpleVocabulary(terms)


class DocumentInSelectedDossierVocabularyFactory(grok.GlobalUtility):
    """ Provides a vocabulary containing all documents within the previously
    selected dossier. Expects the context to be a dict containing the path
    to the dossier under the key 'source_dossier'
    """
    grok.provides(IVocabularyFactory)
    grok.name('opengever.ogds.base.DocumentInSelectedDossierVocabulary')

    def __call__(self, context):
        request = getRequest()
        terms = []


        info = getUtility(IContactInformation)
        comm = getUtility(IClientCommunicator)
        home_clients = info.get_assigned_clients()

        # get client
        client_id = request.get(
            'client', request.get('form.widgets.client'))
        if type(client_id) in (list, tuple, set):
            client_id = client_id[0]
        client = info.get_client_by_id(client_id)

        if client not in home_clients:
            raise ValueError('Expected %s to be a ' % client_id + \
                                 'assigned client of the current user.')

        # get dossier path
        dossier_path = request.get(
            'dossier_path', request.get('form.widgets.source_dossier'))
        if type(dossier_path) in (list, tuple, set):
            dossier_path = dossier_path[0]

        if dossier_path:
            cid = client.client_id
            if cid:
                for doc in comm.get_documents_of_dossier(cid, dossier_path):
                    key = doc.get('path')
                    value = doc.get('title')
                    terms.append(SimpleVocabulary.createTerm(key, key, value))
        # XXX: remove sorting as soon as autocomplete widget is used
        terms.sort(lambda a,b:cmp(a.title, b.title))
        return SimpleVocabulary(terms)
