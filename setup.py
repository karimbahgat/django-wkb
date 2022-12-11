try: from setuptools import setup
except: from distutils.core import setup

setup(	long_description="Django WKB allows efficiently storing and retrieving vector geometries as Well Known Binary data in a Django application.", #open("README.rst").read(), 
	name="""Django WKB""",
	license="""MIT""",
	author="""Karim Bahgat""",
	author_email="""karim.bahgat.norway@gmail.com""",
	version="""0.1.0""",
	keywords="""Django WKB""",
	packages=['djangowkb'],
    install_requires=[
	],
	url='https://github.com/karimbahgat/django-wkb',
	classifiers=['License :: OSI Approved', 'Programming Language :: Python', 'Development Status :: 4 - Beta', 'Intended Audience :: Developers', 'Intended Audience :: Science/Research', 'Intended Audience :: End Users/Desktop'],
	description="""Django WKB allows efficiently storing and retrieving vector geometries as Well Known Binary data in a Django application.""",
	)
