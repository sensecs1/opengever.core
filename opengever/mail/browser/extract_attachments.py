from five import grok
from ftw.mail.mail import IMail
from ftw.mail.utils import get_attachments
from ftw.mail.utils import get_filename
from ftw.mail.utils import remove_attachments
from ftw.table.interfaces import ITableGenerator
from opengever.base.utils import disable_edit_bar
from opengever.base.utils import find_parent_dossier
from opengever.mail import _
from opengever.mail.events import AttachmentsDeleted
from opengever.mail.interfaces import IAttachmentsDeletedEvent
from plone import api
from plone.dexterity.utils import createContentInContainer
from plone.dexterity.utils import iterSchemata
from plone.i18n.normalizer.interfaces import IIDNormalizer
from Products.statusmessages.interfaces import IStatusMessage
from z3c.form.interfaces import IValue
from z3c.relationfield.relation import RelationValue
from zope.component import getUtility
from zope.component import queryMultiAdapter
from zope.event import notify
from zope.intid.interfaces import IIntIds
from zope.lifecycleevent import Attributes
from zope.schema import getFieldsInOrder
import os.path
import re


from plone.namedfile.interfaces import HAVE_BLOBS
if HAVE_BLOBS:
    from plone.namedfile import NamedBlobFile as NamedFile
else:
    from plone.namedfile import NamedFile


def attachment_checkbox_helper(item, position):
    attrs = {'type': 'checkbox',
             'class': 'noborder selectable',
             'name': 'attachments:list',
             'id': 'attachment%s' % str(position),
             'value': str(position)}

    return '<input %s />' % ' '.join(['%s="%s"' % (k, v)
                                      for k, v in attrs.items()])


def content_type_helper(item, content_type):
    """Display the content type icon.
    """
    mtr = api.portal.get_tool(name='mimetypes_registry')
    normalize = getUtility(IIDNormalizer).normalize

    css_class = 'icon-dokument_verweis'
    if content_type == 'application/octet-stream':
        mimetype = mtr.globFilename(item.get('filename'))
    else:
        result = mtr.lookup(content_type)
        if result and isinstance(result, tuple):
            mimetype = result[0]

    if mimetype:
        # Strip '.gif' from end of icon name and remove leading 'icon_'
        icon_filename = mimetype.icon_path
        filetype = os.path.splitext(icon_filename)[0].replace('icon_', '')
        css_class = 'icon-{}'.format(normalize(filetype))

    return '<span class={} />'.format(css_class)


def downloadable_filename_helper(context):
    """Render filename as a download link
    """

    def _helper(item, filename):
        link = '<a href="%s/get_attachment?position=%s">%s</a>' % (
            context.absolute_url(),
            item.get('position'),
            filename)

        transformer = api.portal.get_tool('portal_transforms')
        link = transformer.convertTo('text/x-html-safe', link).getData()
        return link

    return _helper


def human_readable_filesize_helper(context):
    """Render a filesize human readable (e.g. 100 kB)
    """

    def _helper(item, size):
        return context.getObjSize(size=size)

    return _helper


class ExtractAttachments(grok.View):
    """View for extracting attachments from a `ftw.mail` Mail object into
    `opengever.document` Documents in a `IMailInAddressMarker` container.
    """

    grok.context(IMail)
    grok.name('extract_attachments')
    grok.require('zope2.View')
    grok.template('extract_attachments')

    allowed_delete_actions = ('nothing', 'all', 'selected')

    def render_attachment_table(self):
        """Renders a ftw-table of attachments.
        """

        columns = (
            {'column': 'position',
             'column_title': _(u'column_attachment_checkbox',
                               default=u''),
             'transform': attachment_checkbox_helper},

            {'column': 'content-type',
             'column_title': _(u'column_attachment_type',
                               default=u'Type'),
             'transform': content_type_helper},

            {'column': 'filename',
             'column_title': _(u'column_attachment_filename',
                               default=u'Filename'),
             'transform': downloadable_filename_helper(self.context)},

            {'column': 'size',
             'column_title': _(u'column_attachment_size',
                               default=u'Size'),
             'transform': human_readable_filesize_helper(self.context)},
            )

        items = get_attachments(self.context.msg)

        generator = getUtility(ITableGenerator, 'ftw.tablegenerator')
        return generator.generate(items, columns, sortable=False)

    def __call__(self):
        disable_edit_bar()

        items = get_attachments(self.context.msg)
        if not len(items):
            msg = _(u'error_no_attachments_to_extract',
                    default=u'This mail has no attachments to extract.')
            IStatusMessage(self.request).addStatusMessage(msg, type='warning')
            return self.request.RESPONSE.redirect(
                self.context.absolute_url())

        elif self.request.get('form.cancelled'):
            return self.request.RESPONSE.redirect(
                self.context.absolute_url())

        elif self.request.get('form.submitted'):
            attachments = self.request.get('attachments')
            if not attachments:
                msg = _(u'error_no_attachments_selected',
                        default=u'You have not selected any attachments.')
                IStatusMessage(self.request).addStatusMessage(msg,
                                                              type='error')
            else:
                attachments = [int(pos) for pos in attachments]
                delete_action = self.request.get('delete_action', 'nothing')
                if delete_action not in self.allowed_delete_actions:
                    raise ValueError('Expected delete action to be one of ' +
                                         str(self.allowed_delete_actions))

                self.extract_attachments(attachments, delete_action)

                dossier = find_parent_dossier(self)
                return self.request.RESPONSE.redirect(
                    os.path.join(dossier.absolute_url(), '#documents'))

        return grok.View.__call__(self)

    def extract_attachments(self, positions, delete_action):
        dossier = find_parent_dossier(self)

        attachments_to_extract = filter(
            lambda att: att.get('position') in positions,
            get_attachments(self.context.msg))

        # create documents from the selected attachments
        for att in attachments_to_extract:
            pos = att.get('position')
            filename = att.get('filename')

            # remove line breaks from the filename
            filename = re.sub('\s{1,}', ' ', filename)

            kwargs = {'title': filename[:filename.rfind('.')].decode('utf-8'),
                      'file': self.get_attachment_as_namedfile(pos),
                      'keywords': (),
                      'digitally_available': True}

            doc = createContentInContainer(dossier,
                                           'opengever.document.document',
                                           **kwargs)

            for schemata in iterSchemata(doc):
                for name, field in getFieldsInOrder(schemata):
                    if name not in kwargs.keys():
                        default = queryMultiAdapter((
                                doc,
                                doc.REQUEST,  # request
                                None,  # form
                                field,
                                None,  # Widget
                                ), IValue, name='default')
                        if default is not None:
                            default = default.get()
                        if default is None:
                            default = getattr(field, 'default', None)
                        if default is None:
                            try:
                                default = field.missing_value
                            except:
                                pass
                        field.set(field.interface(doc), default)

            # add a reference from the attachment to the mail
            intids = getUtility(IIntIds)
            iid = intids.getId(self.context)

            # prevent circular dependencies
            from opengever.document.behaviors.related_docs import IRelatedDocuments
            IRelatedDocuments(doc).relatedItems = [RelationValue(iid)]

            msg = _(u'info_extracted_document',
                    default=u'Created document ${title}',
                    mapping={'title': doc.Title().decode('utf-8')})
            IStatusMessage(self.request).addStatusMessage(msg, type='info')

            # reindex the new document to index also all the default values
            doc.reindexObject()

        # delete the attachments from the email message, if needed
        if delete_action in ('all', 'selected'):
            if delete_action == 'selected':
                pos_to_delete = positions
            else:
                # all
                pos_to_delete = [int(att['position']) for att in
                                 get_attachments(self.context.msg)]

            attachment_names = [
                a.get('filename', '[no filename]').decode('utf-8')
                for a in get_attachments(self.context.msg)
                if a.get('position') in pos_to_delete]

            # Flag the `message` attribute as having changed
            desc = Attributes(IAttachmentsDeletedEvent, "message")
            notify(AttachmentsDeleted(self.context, attachment_names, desc))

            # set the new message file
            msg = remove_attachments(self.context.msg, pos_to_delete)
            self.context.message = NamedFile(
                data=msg.as_string(),
                contentType=self.context.message.contentType,
                filename=self.context.message.filename)

    def get_attachment_as_namedfile(self, pos):
        """Return a namedfile extracted from the attachment in
        position `pos`.
        """

        # get attachment at position pos
        attachment = None
        for i, part in enumerate(self.context.msg.walk()):
            if i == pos:
                attachment = part
                continue

        if not attachment:
            return None

        # decode when it's necessary
        filename = get_filename(attachment)
        if not isinstance(filename, unicode):
            filename = filename.decode('utf-8')

        # remove line breaks from the filename
        filename = re.sub('\s{1,}', ' ', filename)

        return NamedFile(data=attachment.get_payload(decode=1),
                         contentType=attachment.get_content_type(),
                         filename=filename)
