
from setuptools import find_packages, setup


version = open('Ctl/VERSION').read().strip()
requirements = open('Ctl/requirements.txt').read().split("\n")
test_requirements = open('Ctl/requirements-test.txt').read().split("\n")


setup(
    name='django-namespace-perms',
    version=version,
    author='20C',
    author_email='code@20c.com',
    description='granular permissions for django',
    long_description='',
    license='LICENSE.txt',
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: Apache Software License',
    ],
    packages = find_packages(),
    include_package_data=True,
    url='https://github.com/20c/django-namespace-perms',
    download_url='https://github.com/20c/django-namespace-perms/%s' % version,

    install_requires=requirements,
    test_requires=test_requirements,

    zip_safe=True
)
