import bpy
import random
import math
from mathutils import Euler, Vector
import os

output_dir = r"C:\Users\fai_r\Downloads\blender_tests"
images_dir = os.path.join(output_dir, "images")
labels_dir = os.path.join(output_dir, "labels")
os.makedirs(images_dir, exist_ok=True)
os.makedirs(labels_dir, exist_ok=True)
scene = bpy.context.scene
chair = bpy.data.objects.get("Chair")
floor_half_size = 10
num_images = 50

def randomize_chair(chair):
    x_pos = random.uniform(-floor_half_size, floor_half_size)
    y_pos = random.uniform(-floor_half_size, floor_half_size)
    chair.location = (x_pos, y_pos, 0) 

    rot_x = random.uniform(0, 2*math.pi)
    rot_y = random.uniform(0, 2*math.pi)
    rot_z = random.uniform(0, 2*math.pi)
    chair.rotation_euler = Euler((rot_x, rot_y, rot_z), 'XYZ')

# transform each 3D global point into 2D relative to the camera   
def world_to_camera_view(camera, coord):
    co_local = camera.matrix_world.normalized().inverted() @ coord 
    z = -co_local.z
    
    camera_data = camera.data
    frame = camera_data.view_frame(scene=scene)
    
    # retrieve camera view frame corners 
    left = frame[0].x
    right = frame[1].x
    bottom = frame[2].y
    top = frame[0].y
    
    width = right - left
    height = top - bottom
    if width == 0 or height == 0:
        return Vector((0.5, 0.5, 0.0))  # fallback center point
    
    # normalize to a range relative to the camera's frame boundaries
    x = (co_local.x - left) / width
    y = (co_local.y - bottom) / height
    
    return Vector((x, y, z))

def get_bounding_box_2d(obj, cam):
    mat_world = obj.matrix_world
    coords_3d = [mat_world @ Vector(corner) for corner in obj.bound_box] # from local space to global space
    coords_2d = [world_to_camera_view(cam, coord) for coord in coords_3d] # normalized 2D camera coordinates

    x_vals = [coord.x for coord in coords_2d] # extract x coordinates
    y_vals = [coord.y for coord in coords_2d]

    min_x = max(min(x_vals), 0.0) # leftmost corner
    max_x = min(max(x_vals), 1.0) # rightmost corner
    min_y = max(min(y_vals), 0.0)
    max_y = min(max(y_vals), 1.0)

    mid_x = (min_x + max_x) / 2 # center of bounding box
    mid_y = (min_y + max_y) / 2
    width = max_x - min_x
    height = max_y - min_y

    return mid_x, mid_y, width, height

scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.image_settings.file_format = 'PNG'

def is_bbox_in_view(bbox):
    mid_x, mid_y, width, height = bbox
    # check if bounding box intersects with the normalized camera view area
    if (mid_x + width / 2 < 0) or (mid_x - width / 2 > 1):
        return False
    if (mid_y + height / 2 < 0) or (mid_y - height / 2 > 1):
        return False
    return True

class_id = 0
for i in range(num_images):
    while True:
        randomize_chair(chair)
        bbox = get_bounding_box_2d(chair, bpy.data.objects['Camera'])
        if is_bbox_in_view(bbox):
            break
    center_x, center_y, width, height = bbox

    # render image
    image_path = os.path.join(images_dir, f"img_{i+1}.png")
    scene.render.filepath = image_path
    bpy.ops.render.render(write_still=True)

    label_path = os.path.join(labels_dir, f"label_{i+1}.txt")
    with open(label_path, "w") as label_file:
        label_file.write(f"{class_id} {center_x:.6f} {center_y:.6f} {width:.6f} {height:.6f}\n")
