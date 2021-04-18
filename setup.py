from setuptools import setup, find_packages
import ddd

setup(

    name = 'ddd',
    package = 'ddd',
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
        "CairoSVG >= 2.4.2",
        "freetype-py >= 2.1.0.post1",
        #"GDAL >= 2.2.3",
        "GDAL == 2.2.3",
        "geographiclib >= 1.50",
        "geojson >= 2.5.0",
        "lark-parser >= 0.8.5",
        "networkx >= 2.2",
        "noise >= 1.2.2",
        "numpy < 1.20.0",
        "open3d >= 0.11.2",
        "pandas < 1.2.0",
        "pint >= 0.12",
        "pycsg >= 0.3.3",
        "pyGeoTile >= 1.0.6",
        "pyglet >= 1.4.0b1",
        "PyOpenGL == 3.1.0",
        "PyOpenGL-accelerate == 3.1.5",
        "pypng >= 0.0.20",
        "pyproj < 3.0.0",
        #"pyrender >= 0.1.45",  # optional, doesn't install on containers
        "scipy < 1.6.0",
        "Shapely >= 1.6.4.post2",
        "trimesh[all] >= 3.5.0",  # -e git+https://github.com/mikedh/trimesh.git@8c5633028984b4abb1b7911208f7652119a3c96d#egg=trimesh
        "triangle >= 20190115.3",

        'matplotlib < 3.4',
        'svgpath2mpl >= 0.2.1',
        'svgpathtools >= 1.3.3',

        "osmium >= 2.15.4",
    ],

    entry_points={'console_scripts': ['ddd=ddd.core.cli:main']},
)

