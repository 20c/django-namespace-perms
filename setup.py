from setuptools import setup

version = open('config/VERSION').read().strip()
requirements = open('config/requirements.txt').read().split("\n")

setup(
    name='django-namespace-perms',
    version=version,
    author='Twentieth Century',
    author_email='code@20c.com',
    description='granular permission system that allows permissioning for read / write operations all the way down to the field level. Also supports completely arbitrary / custom permission namespaces.',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    packages=[
      'django_namespace_perms', 
      'django_namespace_perms.auth'
    ],
    url = 'https://github.com/20c/django-namespace-perms',
    download_url = 'https://github.com/20c/django-namespace-perms/%s'%version,
    include_package_data=True,
    install_requires=requirements,
    zip_safe=False
)
