from Products.CMFCore.utils import getToolByName
from opengever.dossier.behaviors.dossier import IDossier
from opengever.ogds.base.utils import get_current_client
from opengever.repository.interfaces import IRepositoryFolder
from Products.CMFPlone.interfaces.siteroot import IPloneSiteRoot
from Acquisition import aq_inner, aq_parent
from opengever.base.interfaces import ISequenceNumber
from opengever.base.interfaces import IReferenceNumber
from ftw.table import helper
from opengever.task.helper import task_type_helper
from opengever.latex.template import LatexTemplateFile
from opengever.latex.views.baselisting import BasePDFListing
from opengever.ogds.base.interfaces import IContactInformation
from zope.component import getUtility


class DossierDetailsPDF(BasePDFListing):
    """Create a PDF with dossier details.
    """

    main = LatexTemplateFile('dossierdetails_main.tex')
    tasks = LatexTemplateFile('dossierdetails_tasks.tex')
    documents = LatexTemplateFile('dossierdetails_documents.tex')
    subdossiers = LatexTemplateFile('dossierdetails_subdossiers.tex')

    def render(self):
        return self.main(tasks=self.get_tasks_latex(),
                         documents=self.get_documents_latex(),
                         subdossiers=self.get_subdossiers_latex(),
                         **self.get_main_options())

    def get_main_options(self):
        """Returns a dict of options for the main details table.
        """

        client = get_current_client()
        info = getUtility(IContactInformation)
        data = {}

        dossier = IDossier(self.context)

        data['reference'] = IReferenceNumber(self.context).get_number()
        seq = getUtility(ISequenceNumber)
        data['sequence'] = str(seq.get_number(self.context))
        data['filing_no'] = str(getattr(self.context, 'filing_no', ''))

        # buildout a kind of breadcrumbs with all parental repository folders
        repository = []
        parent = aq_parent(aq_inner(self.context))
        while not IPloneSiteRoot.providedBy(parent):
            if IRepositoryFolder.providedBy(parent):
                repository.append(parent.Title())
            parent = aq_parent(aq_inner(parent))

        data['repository'] = ' / '.join(repository)

        data['title'] = self.context.Title()
        state = self.context.restrictedTraverse('@@plone_context_state')
        data['review_state'] = self.context.translate(state.workflow_state(),
                                                      domain='plone')

        data['responsible'] = ' '.join(
            (str(client.title), info.describe(dossier.responsible)))
        data['participation'] = '? ? ? ? ?'

        data['start'] = helper.readable_date(self.context, dossier.start)
        data['end'] = helper.readable_date(self.context, dossier.end)

        # convert to latex
        return dict([(key, self.convert(value))
                     for key, value in data.items()])

    def _prepare_table_row(self, *cells):
        """Converts every cell in `cells` into LaTeX and merges them
        to a LaTeX row.
        """

        return ' & '.join([self.convert(cell) for cell in cells])

    def get_tasks_latex(self):
        """Returns the latex containing all tasks which are within
        this dossier - or an empty string if there are none.
        """

        rows = []
        task_marker = 'opengever.task.task.ITask'

        # make the query
        catalog = getToolByName(self.context, 'portal_catalog')
        brains = catalog({'path': '/'.join(self.context.getPhysicalPath()),
                          'object_provides': task_marker})

        # any results?
        if len(brains) == 0:
            return ''

        info = getUtility(IContactInformation)

        # create rows in latex
        for brain in brains:

            rows.append(self._prepare_table_row(
                    str(brain.sequence_number),
                    task_type_helper(brain, brain.task_type),
                    info.describe(brain.issuer),
                    info.describe(brain.responsible),
                    self.context.translate(brain.review_state,
                                           domain='plone'),
                    str(brain.Title),
                    helper.readable_date(brain, brain.deadline),
                    ))

        return self.tasks(rows='\\\\ \\hline\n'.join(rows))

    def get_documents_latex(self):
        """Returns the latex containing all documents which are within
        this dossier - or an empty string if there are none.
        """

        rows = []
        documents_marker = 'opengever.document.document.IDocumentSchema'

        # make the query
        catalog = getToolByName(self.context, 'portal_catalog')
        brains = catalog({'path': '/'.join(self.context.getPhysicalPath()),
                          'object_provides': documents_marker})

        # any results?
        if len(brains) == 0:
            return ''

        # create rows in latex
        for brain in brains:

            rows.append(self._prepare_table_row(
                    str(brain.sequence_number),
                    str(brain.Title),
                    helper.readable_date(brain, brain.document_date),
                    ))

        return self.documents(rows='\\\\ \\hline\n'.join(rows))

    def get_subdossiers_latex(self):
        """Returns the latex containing all subdossiers which are within
        this dossier - or an empty string if there are none.
        """

        rows = []
        dossier_marker = 'opengever.dossier.behaviors.dossier.IDossierMarker'

        # make the query
        catalog = getToolByName(self.context, 'portal_catalog')
        brains = catalog({'path': '/'.join(self.context.getPhysicalPath())+'/',
                          'object_provides': dossier_marker})

        # filter the brain of self.context
        context_path = '/'.join(self.context.getPhysicalPath())
        brains = filter(lambda brain: brain.getPath() != context_path,
                        brains)

        # any results?
        if len(brains) == 0:
            return ''

        info = getUtility(IContactInformation)

        # create rows in latex
        for brain in brains:

            rows.append(self._prepare_table_row(
                    str(brain.sequence_number),
                    str(brain.reference),
                    str(brain.Title),
                    info.describe(brain.responsible),
                    self.context.translate(brain.review_state,
                                           domain='plone'),
                    helper.readable_date(brain, brain.start),
                    ))

        return self.subdossiers(rows='\\\\ \\hline\n'.join(rows))
