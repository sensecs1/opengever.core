from setuptools import setup, find_packages
import os

version = open('opengever/dossier/version.txt').read().strip()
maintainer = 'Thomas Buchberger'

tests_require = [
    'collective.testcaselayer',
]

setup(name='opengever.dossier',
      version=version,
      description="OpenGever Dossier Content Types (Maintainer: %s)" % maintainer,
      long_description=open("README.txt").read() + "\n" + \
          open(os.path.join("docs", "HISTORY.txt")).read(),
      # Get more strings from http://www.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
        "Framework :: Plone",
        "Framework :: Zope2",
        "Framework :: Zope3",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
      keywords='OpenGever Dossier',
      author='%s, 4teamwork GmbH' % maintainer,
      author_email='mailto:info@4teamwork.ch',
      url='http://psc.4teamwork.ch/4teamwork/kunden/opengever/opengever.dossier/',
      license='GPL2',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['opengever'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
        'setuptools',
        'plone.app.dexterity',
        'plone.app.registry',
        'ftw.datepicker',
        'collective.autopermission',
        'opengever.base',
        'rwproperty',
        'plonegov.pdflatex>=0.2.6',
        'opengever.mail',
        # -*- Extra requirements: -*-
        ],
      tests_require=tests_require,
      extras_require=dict(tests=tests_require),
      entry_points="""
      # -*- Entry points: -*-
      [z3c.autoinclude.plugin]
      target = plone
      """,
      )
