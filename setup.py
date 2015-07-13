from setuptools import setup, find_packages

setup(name='pythalesians',
      version='0.1a',
      description='Financial analysis library',
      author='Saeed Amen',
      author_email='saeed@thalesians.com',
      license='Apache 2.0',
      keywords = ['pandas', 'bloomberg', 'plot'],
      url = 'https://github.com/thalesians/pythalesians',
      packages = find_packages(),
      include_package_data = True,
      install_requires = ['pandas',
                          'matplotlib',
                          'twython',
                          'pytz',
                          'requests',
                          'numpy'],
	  zip_safe=False)