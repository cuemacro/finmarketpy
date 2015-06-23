from setuptools import setup

setup(name='pythalesians',
      version='0.1a',
      description='Financial analysis library',
      author='Saeed Amen',
      author_email='saeed@thalesians.com',
      license='Apache 2.0',
      keywords = ['pandas', 'bloomberg', 'plot'],
      url = 'https://github.com/thalesians/pythalesians',
      packages=['pythalesians'],
      install_requires = ['pandas'],
	  zip_safe=False)