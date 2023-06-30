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
        #"aiohttp < 4.0",
        "aiohttp < 3.8.0",
        "chardet < 4.0",
        "CairoSVG >= 2.4.2",
        "centerline >= 0.6.4",
        "freetype-py >= 2.1.0.post1",
        # Docker image is installing pygdal (not GDAL) - check
        #"GDAL == 3.0.4",  # Ubuntu 20.04 (3.0.4? - docker image is using 2.2.3 (?) Ubuntu 20.04 GDAL is 3.0.4 )
        #"GDAL == 3.4.1",  # Ubuntu 22.04
        "geographiclib >= 1.50",
        "geojson >= 2.5.0",
        "lark-parser >= 0.8.5",
        "networkx >= 2.2",
        "noise >= 1.2.2",
        #"numpy >= 1.20.0",
        "numpy < 1.20",
        "pandas < 1.2.0",
        "Pillow >= 8.2.0",
        "pint == 0.12",
        "portion >= 2.2.0",
        "pycatenary >= 0.4.0",
        "pycsg >= 0.3.3",
        #"pyembree == 0.2.11",  # Used for faster ray casting, used by Trimesh itself (called during osm_generate_building_preprocess)
        "pyGeoTile >= 1.0.6",
        "pyglet < 2",  # < 2 required by trimesh 3.22.1
        #"PyOpenGL",  # == 3.1.0",  # TODO: fails inside docker?
        #"PyOpenGL-accelerate",  # == 3.1.5",  # TODO: fails inside docker?
        "pypng >= 0.0.20",
        "pyproj < 3.0.0",
        "python-socketio",  # >= 5.4.0",
        #"pyrender >= 0.1.45",  # optional, doesn't install on containers
        "scipy < 1.6.0",
        #"Shapely >= 1.8.1.post1",
        "Shapely == 1.8.1.post1",    # Later versions don't allow object assignemnt (our usage of geom._obj_ref for spatial indices)
        "trimesh[all] == 3.15.1",    # Later versions don't have the 'extras' argument in scene.add_geometry, need migration
        "triangle >= 20190115.3",
        "watchdog == 2.1.7",  # for server

        "importlib-metadata",  # < 4",  # required by ipython required by open3D
        #"open3d >= 0.11.2",

        'matplotlib < 3.4',
        'svgpath2mpl >= 1.0.0',
        'svgpathtools >= 1.3.3',

        "osmium >= 2.15.4",
    ],

    entry_points={'console_scripts': ['ddd=ddd.core.cli:main']},
)

