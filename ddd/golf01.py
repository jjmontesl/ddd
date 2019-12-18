
from ddd_sketchy import terrain
from ddd_sketchy import plants
from ddd_sketchy import urban
from ddd import ddd
import random

mat_lane = ddd.material(color='#1db345')
mat_terrain = ddd.material(color='#e6821e')
mat_border = ddd.material(color='#f0f0ff')

hole_r = 0.35

random.seed(1)

def clamp(val, min_value, max_value):
    return max(min(val, max_value), min_value)

def trackA():        
    lane1 = ddd.point([0, 0]).line_rel([0, 20]).line_rel([20, -5, -3]).line_rel([0, -15])
    lane2 = lane1.buffer(4.0)
    lane2 = lane2.union(ddd.disc(lane1.end(), r=7))
    lane3 = lane2.extrude(3.0)
    
    # Hole (shall make a nicer prefab with double border and optional flag?)
    hole3 = ddd.sphere(lane1.end(), hole_r, subdivisions=1)
    #hole3 = hole3.snap(lane3, 'floor', handle='center')
    hole3 = hole3.translate([0, 0, 6])
    lane3 = lane3.subtract(hole3)
    def elevation_func(x, y):
        xr = clamp(x, 4, 4 + 20 - 8) - 4
        return - (xr - 4) * 0.25
    lane3 = lane3.elevation_func(elevation_func)
    
    lane3 = lane3.material(mat_lane)
    
    # Border
    border2 = lane2.buffer(0.5).subtract(lane2)  # outline = grow + subtract
    border3 = border2.extrude(3.25)
    border3 = border3.elevation_func(elevation_func)
    border3 = border3.material(mat_border)
    
    #ddd.group([lane2, border2]).save('/tmp/test.svg')
    
    track3 = ddd.group([lane3, border3])
    return track3

def trackB():        
    lane1 = ddd.point([0, 30]).line_rel([15, 0]).line_rel([15, -5, -3]).line_rel([0, -10, -3]).line_rel([5, -8, 0])
    lane2 = lane1.buffer(4.0, join_style=2)
    lane2 = lane2.union(ddd.disc(lane1.end(), r=7))
    lane3 = lane2.extrude(3.0)
    
    # Hole (shall make a nicer prefab with double border and optional flag?)
    hole3 = ddd.sphere(lane1.end(), hole_r, subdivisions=1)
    #hole3 = hole3.snap(lane3, 'floor', handle='center')
    hole3 = hole3.translate([0, 0, 9])
    lane3 = lane3.subtract(hole3)
    def elevation_func(x, y):
        xr = clamp(x, 4, 4 + 20 - 8) - 4
        return - (xr - 4) * 0.5 + 2
    
    lane3 = lane3.elevation_func(elevation_func)
    
    lane3 = lane3.material(mat_lane)
    
    # Border
    border2 = lane2.buffer(0.5).subtract(lane2)  # outline = grow + subtract
    border3 = border2.extrude(3.25)
    border3 = border3.elevation_func(elevation_func)
    border3 = border3.material(mat_border)
    
    #ddd.group([lane2, border2]).save('/tmp/test.svg')
    
    track3 = ddd.group([lane3, border3])
    return track3

trackA3 = trackA()
trackB3 = trackB()
track3 = ddd.group([trackA3, trackB3])


#track3 = ddd.floatingblocks.extrude_down(track3, add_vertexes=True, max_height=-10)

surroundings = terrain.terrain_grid(distance=40.0, height=5.0, detail=2.0, scale=0.151273).translate([20, 20, -2.0]).material(mat_terrain)
#surroundings = surroundings.extrude(1)
#surroundings = terrain.generate_around(lane3, min_height=1.0, max_height=2.0).material(mat_terrain)
#floatingblocks = ddd.floatingblocks.random_blocks(min_z=-15, max_z=15, max_height=8, avoid_collisions=True).material(mat_terrain)
#trees = ddd.populate.place_over(tree, [surroundings, randomblocks])  
tree = plants.plant(height=7.0, fork_iters=5).translate([21, 21, -1.0])
fountain = urban.fountain().translate([35, 35, -0.5])

scenery3 = ddd.group([surroundings, tree, fountain])  # , blocks, trees

scene = ddd.group([track3, scenery3])
#scene.save()
scene.show()
scene.save('golf01.gltf')
scene.save('golf01.dae')

