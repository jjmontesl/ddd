from setuptools import setup, find_packages
import ddd

setup(

    name = 'ddd123',
    package = 'ddd123',
    version = ddd.APP_VERSION,

    author = 'Jose Juan Montes',
    author_email = 'jjmontes@gmail.com',

    packages = find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),

    zip_safe=False,
    include_package_data=True,
    package_data = {
        #'sitetool': ['*.template']
    },

    #url='',
    license='LICENSE.txt',
    description='Use paths, shapes and geometries in order to produce 3D scenes.',
    long_description="Use paths, shapes and geometries in order to produce 3D scenes.",

    classifiers = [
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Programming Language :: Python',
        'Topic :: Database',
        'Topic :: Utilities',
    ],

    install_requires = [
        "GDAL >= 2.2.3",
        "geographiclib >= 1.50",
        "geojson >= 2.5.0",
        #"MeshPy >= 2018.2.1",
        "pyproj >= 2.4.2.post1",
        "pycsg >= 0.3.3",
        "Shapely >= 1.6.4.post2",
        "trimesh >= 3.5.0",

        'svgpath2mpl >= 0.2.1',
        'svgpathtools >= 1.3.3',

    ],

    entry_points={'console_scripts': ['ddd=ddd.core.cli:main']},
)

