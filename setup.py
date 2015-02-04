
from setuptools import setup

setup(
    name='django-namespace-perms',
    version='0.1',
    author='Twentieth Century',
    author_email='code@20c.com',
    description='granular permission system that allows permissioning for read / write operations all the way down to the field level. Also supports completely arbitrary / custom permission namespaces.',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    packages=['django_namespace_perms', 'django_namespace_perms.auth'],
    include_package_data=True,
    install_requires=open("requirements.txt").read().split("\n"),
    zip_safe=False
)
