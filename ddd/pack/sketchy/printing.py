# ddd - D1D2D3
# Library for simple scene modelling.
# Jose Juan Montes 2020

import logging

from ddd.ddd import ddd
from trimesh import transformations
from ddd.math.vector3 import Vector3

from ddd.ops.layout import DDDLayout, VerticalDDDLayout
from ddd.pack.shapes.holes import hole_broken


# Get instance of logger for this module
logger = logging.getLogger(__name__)


def poster_flat(width=0.4, height=0.6):
    """
    Poster is upright centered and facing -Y, on the XY plane.
    """
    poster = ddd.rect([width, height], name="Poster")
    poster = poster.triangulate().twosided()
    poster = poster.material(ddd.MAT_TEST)  # ddd.mats.paper_coarse)
    poster = ddd.uv.map_cubic(poster, scale=[1 / width, 1 / height])
    poster = poster.rotate(ddd.ROT_FLOOR_TO_FRONT).translate([-width/2, 0, 0])
    return poster

def poster_fold(width=0.4, height=0.6):
    """
    Poster with a fold on a corner.
    """
    pass


def poster_wrinkled(width=0.4, height=0.6):
    """
    Poster with wrinkles
    """
    pass



def poster_ripped(width=0.4, height=0.6, hole_size_n=[0.5, 0.4], hole_center_n=[0.9, 0.1]):
    """
    Poster with a missing (teared apart) part. UVs are mapped to the full poster so the image it appears ripped.
    """
    poster = ddd.rect([width, height], name="Poster Ripped")
    hole = hole_broken(hole_size_n[0] * width, hole_size_n[1] * height, noise_scale=hole_size_n[0] * width * 0.1)

    hole = hole.recenter().translate([hole_center_n[0] * width, hole_center_n[1] * height])
    #ddd.group([poster, hole]).show()
    poster = poster.subtract(hole)

    poster = poster.triangulate().twosided()
    poster = poster.material(ddd.MAT_TEST)  # ddd.mats.paper_coarse)
    poster = ddd.uv.map_cubic(poster, scale=[1 / width, 1 / height])
    poster = poster.rotate(ddd.ROT_FLOOR_TO_FRONT).translate([-width/2, 0, 0])
    return poster

def image_posterize():
    pass

def image_age():
    pass


def text_note(width=0.210, height=0.297, text="This note is misteriously empty."):
    """
    A paper note.
    Paper is upright centered and facing -Y.
    """
    item = ddd.rect([width, height], name="Note")
    item = item.triangulate().twosided()
    item = item.material(ddd.mats.paper)
    item = ddd.uv.map_cubic(item, scale=[1 / width, 1 / height])
    item = item.rotate(ddd.ROT_FLOOR_TO_FRONT).translate([-width/2, 0, -height * 0.5])
    item.set('ddd:text', text)
    return item

def text_note_teared(width=0.210, height=0.297, tear_height_norm=0.75, text="This note is misteriously empty."):
    """
    Paper note with a missing part.
    Paper is upright centered and facing -Y. The center is the center of the full note (as if it included the teared off part).
    """
    item = ddd.rect([width, height], name="Note Teared")

    hole = hole_broken(width * 2, height * 2, noise_scale=width * 0.05)
    hole = hole.recenter().translate([width * 0.5, -tear_height_norm * height])

    ddd.group([item, hole]).show()
    item = item.subtract(hole)

    item = item.triangulate().twosided()
    item = item.material(ddd.mats.paper)
    item = ddd.uv.map_cubic(item, scale=[1 / width, 1 / height])
    item = item.rotate(ddd.ROT_FLOOR_TO_FRONT).translate([-width/2, 0, -height * 0.5])
    return item


def frame_table():
    raise NotImplementedError()

def frame_wall():
    raise NotImplementedError()



def book_solid_flat(width=0.16, height=0.23, thick=0.02):
    """
    Books lie on the positive XY plane, facing Z (bottom left back corner is on the origin).
    
    Books UV texturing and slots: TODO
    """
    item = ddd.rect([0, 0, width, height], name="Book")
    item = item.extrude(thick)
    item = item.material(ddd.mats.paper)
    item = ddd.uv.map_cubic(item, scale=[1 / width, 1 / height])
    return item

def book_solid_covers(width=0.16, height=0.23, thick=0.02):
    """
    Books lie on the positive XY plane, facing Z (bottom left back corner is on the origin).
    
    Books UV texturing and slots: TODO
    """
    raise NotImplementedError()

def book_parts():
    """
    """
    raise NotImplementedError()


def book_row_fake():
    """
    Fake books (to fill shelves and save polygons).
    """
    raise NotImplementedError()


BOOK_DATA = [
    # English books
    {'title': 'The Lord of the Rings', 'author': 'J. R. R. Tolkien', 'year': '1954', 'lang': 'en', 'pages': 1178, 'icon': 'ring', 'genre': 'fantasy'},
    {'title': 'The Hobbit', 'author': 'J. R. R. Tolkien', 'year': '1937', 'lang': 'en', 'pages': 310, 'icon': 'dwarf', 'genre': 'fantasy'},
    {'title': 'Harry Potter', 'author': 'J. K. Rowling', 'year': '1997', 'lang': 'en', 'pages': 223, 'icon': 'wizard', 'genre': 'fantasy'},
    {'title': 'The Catcher in the Rye', 'author': 'J. D. Salinger', 'year': '1951', 'lang': 'en', 'pages': 234, 'icon': 'baseball', 'genre': 'drama'},
    {'title': 'The Great Gatsby', 'author': 'F. Scott Fitzgerald', 'year': '1925', 'lang': 'en', 'pages': 218, 'icon': 'martini', 'genre': 'drama'},
    {'title': 'The Lion, the Witch and the Wardrobe', 'author': 'C. S. Lewis', 'year': '1950', 'lang': 'en', 'pages': 206, 'icon': 'lion', 'genre': 'fantasy'},
    {'title': 'The Hunger Games', 'author': 'Suzanne Collins', 'year': '2008', 'lang': 'en', 'pages': 374, 'icon': 'arrow-right', 'genre': 'fantasy'},
    {'title': 'The Chronicles of Narnia', 'author': 'C. S. Lewis', 'year': '1950', 'lang': 'en', 'pages': 206, 'icon': 'lion', 'genre': 'fantasy'}, 
    {'title': 'Animal Farm', 'author': 'George Orwell', 'year': '1945', 'lang': 'en', 'pages': 112, 'icon': 'pig', 'genre': 'drama'},
    {'title': 'The Da Vinci Code', 'author': 'Dan Brown', 'year': '2003', 'lang': 'en', 'pages': 454, 'icon': 'eye', 'genre': 'thriller'},
    {'title': 'The Social Construction of Reality', 'author': 'Peter L. Berger', 'year': '1966', 'lang': 'en', 'pages': 219, 'icon': 'eye', 'genre': 'sociology'},
    {'title': 'The Structure of Scientific Revolutions', 'author': 'Thomas S. Kuhn', 'year': '1962', 'lang': 'en', 'pages': 172, 'icon': 'eye', 'genre': 'science'},
    
    # Technical books in various areas / English
    {'title': 'Advanced XML', 'author': 'Ray Lischner', 'year': '2001', 'lang': 'en', 'pages': 352, 'icon': 'computer', 'genre': 'technical', 'area': 'computer science'},
    {'title': 'Advanced C++', 'author': 'James O. Coplien', 'year': '1992', 'lang': 'en', 'pages': 544, 'icon': 'computer', 'genre': 'technical', 'area': 'computer science'},
    {'title': 'Modern Architecture', 'author': 'Kenneth Frampton', 'year': '1980', 'lang': 'en', 'pages': 320, 'icon': 'building', 'genre': 'technical', 'area': 'architecture'},
    {'title': 'De Architectura', 'author': 'Vitruvius', 'year': '15 BC', 'lang': 'en', 'pages': 352, 'icon': 'building', 'genre': 'technical', 'area': 'architecture'},
    {'title': 'Towards a New Architecture', 'author': 'Le Corbusier', 'year': '1923', 'lang': 'en', 'pages': 320, 'icon': 'building', 'genre': 'technical', 'area': 'architecture'},


    # Spanish books
    {'title': 'El Quijote', 'author': 'Miguel de Cervantes', 'year': '1605', 'lang': 'es', 'pages': 863, 'icon': 'windmill'},
    {'title': 'Cien años de soledad', 'author': 'Gabriel García Márquez', 'year': '1967', 'lang': 'es', 'pages': 422, 'icon': 'sun'},
    {'title': 'Don Juan Tenorio', 'author': 'José Zorrilla', 'year': '1844', 'lang': 'es', 'pages': 159, 'icon': 'skull'},
    {'title': 'La Regenta', 'author': 'Leopoldo Alas Clarín', 'year': '1884', 'lang': 'es', 'pages': 1022, 'icon': 'heart'},
    {'title': 'La Celestina', 'author': 'Fernando de Rojas', 'year': '1499', 'lang': 'es', 'pages': 160, 'icon': 'heart'},
    {'title': 'La vida es sueño', 'author': 'Pedro Calderón de la Barca', 'year': '1635', 'lang': 'es', 'pages': 168, 'icon': 'moon'},
    {'title': 'El Lazarillo de Tormes', 'author': 'Anónimo', 'year': '1554', 'lang': 'es', 'pages': 104, 'icon': 'eye'},
    {'title': 'Poema de mio Cid', 'author': 'Anónimo', 'year': '1207', 'lang': 'es', 'pages': 170, 'icon': 'sword'},
    {'title': 'La Colmena', 'author': 'Camilo José Cela', 'year': '1951', 'lang': 'es', 'pages': 360, 'icon': 'bee'},
    {'title': 'El Buscón', 'author': 'Francisco de Quevedo', 'year': '1626', 'lang': 'es', 'pages': 160, 'icon': 'eye'},
    {'title': 'El Hobbit', 'author': 'J. R. R. Tolkien', 'year': '1937', 'lang': 'es', 'pages': 310, 'icon': 'dwarf'},
    {'title': 'El Señor de los Anillos', 'author': 'J. R. R. Tolkien', 'year': '1954', 'lang': 'es', 'pages': 1178, 'icon': 'eye'},
    {'title': 'Harry Potter', 'author': 'J. K. Rowling', 'year': '1997', 'lang': 'es', 'pages': 223, 'icon': 'wizard'},
    {'title': 'El Principito', 'author': 'Antoine de Saint-Exupéry', 'year': '1943', 'lang': 'es', 'pages': 96, 'icon': 'fox'},
    {'title': 'El alquimista', 'author': 'Paulo Coelho', 'year': '1988', 'lang': 'es', 'pages': 208, 'icon': 'alchemy'},
    {'title': 'El Código Da Vinci', 'author': 'Dan Brown', 'year': '2003', 'lang': 'es', 'pages': 454, 'icon': 'eye'},
    {'title': 'El retrato de Dorian Gray', 'author': 'Oscar Wilde', 'year': '1890', 'lang': 'es', 'pages': 254, 'icon': 'paint-brush'},
    {'title': 'El laberinto de los espíritus', 'author': 'Carlos Ruiz Zafón', 'year': '2016', 'lang': 'es', 'pages': 925, 'icon': 'eye'},
    {'title': 'El arte de la guerra', 'author': 'Sun Tzu', 'year': '400 BC', 'lang': 'es', 'pages': 104, 'icon': 'sword'},


    # French books
    {'title': 'Les Misérables', 'author': 'Victor Hugo', 'year': '1862', 'lang': 'fr', 'pages': 1900, 'icon': 'eye', 'genre': 'drama'},
    {'title': 'Le Petit Prince', 'author': 'Antoine de Saint-Exupéry', 'year': '1943', 'lang': 'fr', 'pages': 96, 'icon': 'fox', 'genre': 'fantasy'},
    {'title': 'Le Comte de Monte-Cristo', 'author': 'Alexandre Dumas', 'year': '1844', 'lang': 'fr', 'pages': 464, 'icon': 'eye', 'genre': 'drama'},
    {'title': 'Notre-Dame de Paris', 'author': 'Victor Hugo', 'year': '1831', 'lang': 'fr', 'pages': 940, 'icon': 'eye', 'genre': 'drama'},
    {'title': 'Le Rouge et le Noir', 'author': 'Stendhal', 'year': '1830', 'lang': 'fr', 'pages': 576, 'icon': 'eye', 'genre': 'drama'},
    {'title': 'Vingt mille lieues sous les mers', 'author': 'Jules Verne', 'year': '1870', 'lang': 'fr', 'pages': 288, 'icon': 'eye', 'genre': 'fantasy'},
    {'title': 'Les Trois Mousquetaires', 'author': 'Alexandre Dumas', 'year': '1844', 'lang': 'fr', 'pages': 704, 'icon': 'eye', 'genre': 'drama'},
    {'title': 'Le Tour du monde en quatre-vingts jours', 'author': 'Jules Verne', 'year': '1873', 'lang': 'fr', 'pages': 256, 'icon': 'eye', 'genre': 'adventure'},
    {'title': 'Le Père Goriot', 'author': 'Honoré de Balzac', 'year': '1835', 'lang': 'fr', 'pages': 443, 'icon': 'eye', 'genre': 'drama'},

    # Chinese books
    
    # 红楼梦 (Dream of the Red Chamber)
    {'title': '红楼梦', 'author': '曹雪芹', 'year': '1791', 'lang': 'zh', 'pages': 2500, 'icon': 'house', 'genre': 'drama'},
    # 西游记 (Journey to the West)
    {'title': '西游记', 'author': '吴承恩', 'year': '1592', 'lang': 'zh', 'pages': 2000, 'icon': 'monkey', 'genre': 'fantasy'},
    # 水浒传 (Outlaws of the Marsh)
    {'title': '水浒传', 'author': '施耐庵', 'year': '1589', 'lang': 'zh', 'pages': 2300, 'icon': 'hero', 'genre': 'drama'},
    # 三国演义 (Romance of the Three Kingdoms)
    {'title': '三国演义', 'author': '罗贯中', 'year': '1522', 'lang': 'zh', 'pages': 2400, 'icon': 'sword', 'genre': 'drama'},
    # 边城 (Border Town)
    {'title': '边城', 'author': '沈从文', 'year': '1934', 'lang': 'zh', 'pages': 180, 'icon': 'river', 'genre': 'drama'},
    # 围城 (Fortress Besieged)
    {'title': '围城', 'author': '钱钟书', 'year': '1947', 'lang': 'zh', 'pages': 430, 'icon': 'wall', 'genre': 'drama'},
    # 家 (Family)
    {'title': '家', 'author': '巴金', 'year': '1933', 'lang': 'zh', 'pages': 300, 'icon': 'tree', 'genre': 'drama'},
    # 骆驼祥子 (Rickshaw Boy)
    {'title': '骆驼祥子', 'author': '老舍', 'year': '1936', 'lang': 'zh', 'pages': 250, 'icon': 'cart', 'genre': 'drama'},
    # 活着 (To Live)
    {'title': '活着', 'author': '余华', 'year': '1993', 'lang': 'zh', 'pages': 250, 'icon': 'life', 'genre': 'drama'},


]

