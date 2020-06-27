import setuptools


with open('requirements.txt') as f:
    requirements = f.read().splitlines()

with open('README.md') as f:
    readme = f.read()


setuptools.setup(
    name='diorite',
    author='twitch0001 and MyNameBeMrRandom',
    version='0.1.1',
    url='https://github.com/iDevision/diorite',
    packages=setuptools.find_packages(),
    license='APGL-3.0',
    description='A python wrapper for LavaLink intended for use with discord.py.',
    long_description=readme,
    long_description_content_type='text/markdown',
    include_package_data=True,
    install_requires=requirements,
    classifiers=[
        'Framework :: AsyncIO',
        'Natural Language :: English',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Software Development :: Libraries',
        'Topic :: Internet'
    ],
    python_requires='>=3.7',
    keywords=['discord.py', 'lavalink'],
)
