# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import logging
import math
import sys

from ddd.ddd import ddd, DDDObject3, DDDObject, DDDObject2
from ddd.core.cli import D1D2D3Bootstrap
from multiprocessing import Process, Queue

# Get instance of logger for this module
logger = logging.getLogger(__name__)

_thread = None
_viewer = None
#_scene = None
_queue = Queue()

def showbg(obj):
    """
    An "inverted" update loop.

    Scene is updated each time showbg() is called.
    """

    from trimesh.viewer.windowed import SceneViewer

    if D1D2D3Bootstrap.renderer != 'pyglet':
        logger.debug("Ignoring 'showbg' (only supported with pyglet renderer, try --help).")
        return

    logger.info("Showing in background: %s", obj)

    # OpenGL
    if isinstance(obj, DDDObject2):
        obj = obj.triangulate()

    rotated = obj.rotate([-math.pi / 2.0, 0, 0])
    scene = rotated._recurse_scene("", "", instance_mesh=True, instance_marker=False)

    global _viewer
    global _thread
    #global _scene

    #_scene = scene

    def _update_callback(scene):
        #global _scene
        #global _viewer
        if scene.geometry != _scene.geometry:
            print("Pyglet callback called: %s" % (scene))
            scene.geometry = _scene.geometry
        #if _viewer:
        #    _viewer.cleanup_geometries()
        #    _viewer._update_meshes()

    def _pyglet_thread_run():
        # this imports pyglet, and will raise an ImportError
        # if pyglet is not available
        #global _viewer

        _viewer = SceneViewer(scene, callback=_update_callback)

    if _thread is None:
        #_thread = Thread(target=_pyglet_thread_run)
        #_thread.start()
        _thread = Process(target=_pyglet_thread_run)
        _thread.start()

    _queue.put(scene)

    '''
    elif _viewer:
        _viewer.scene = scene
        _viewer._scene = scene
        _viewer.scene._redraw = _viewer._redraw
        _viewer._update_vertex_list()
        _viewer._redraw()
    '''








