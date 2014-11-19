from plone.app.layout.globals.layout import LayoutPolicy


class DocumentishLayoutPolicy(LayoutPolicy):

    def bodyClass(self, template, view):
        """Extends the default body class with the `removed` class, when
        document is removed. Used for different styling when the document is
        removed.
        """

        body_class = super(DocumentishLayoutPolicy, self).bodyClass(
            template, view)

        if self.context.is_trashed:
            body_class = '{} removed'.format(body_class)

        return body_class
