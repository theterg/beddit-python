from setuptools import setup

setup(
    name = "Beddit",
    version = "0.1",
    packages = find_packages(),
    #scripts = [],
    install_requires = ['requests>=2.0'],
    extras_require = {
        'numpy': ['numpy>=1.3.0'],
    },
    #package_data = {},

    author = "Andrew Tergis",
    author_email = "theterg@gmail.com",
    description = "A thin Python wrapper for the Beddit API",
    license = "Freely Distributable",
    keywords = "beddit api sleep",
    #entry_points = {
    #    'console_scripts': [
    #        'beddit_scrape = my_package.some_module:main_func'
    #    ]
    #},
)