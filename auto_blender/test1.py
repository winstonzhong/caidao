import bpy
import mathutils

def get_model_bounding_box_vertices(obj_name):
    """
    计算模型的最小外接立方体（AABB）的所有顶点坐标
    
    参数:
        obj_name: 模型对象的名称
    
    返回:
        包含8个顶点坐标的列表，每个顶点是一个mathutils.Vector
    """
    obj = bpy.data.objects.get(obj_name)
    if not obj:
        print(f"❌ 对象 {obj_name} 不存在")
        return []
    
    # 获取对象的边界框（8个顶点的局部坐标）
    local_bbox_coords = [mathutils.Vector(v) for v in obj.bound_box]
    
    # 将局部坐标转换为世界坐标
    world_bbox_coords = [obj.matrix_world @ v for v in local_bbox_coords]
    
    # 也可以通过计算每个维度的最小值和最大值来获取边界框
    # 这在某些情况下可能更有用（例如需要自定义边界框大小时）
    min_coords = [min(v[i] for v in world_bbox_coords) for i in range(3)]
    max_coords = [max(v[i] for v in world_bbox_coords) for i in range(3)]
    
    # 生成8个顶点的坐标（通过组合每个维度的最小值和最大值）
    vertices = [
        mathutils.Vector((min_coords[0], min_coords[1], min_coords[2])),
        mathutils.Vector((max_coords[0], min_coords[1], min_coords[2])),
        mathutils.Vector((max_coords[0], max_coords[1], min_coords[2])),
        mathutils.Vector((min_coords[0], max_coords[1], min_coords[2])),
        mathutils.Vector((min_coords[0], min_coords[1], max_coords[2])),
        mathutils.Vector((max_coords[0], min_coords[1], max_coords[2])),
        mathutils.Vector((max_coords[0], max_coords[1], max_coords[2])),
        mathutils.Vector((min_coords[0], max_coords[1], max_coords[2]))
    ]
    
    return vertices

def print_bounding_box_vertices(obj_name):
    """打印模型边界框顶点信息"""
    vertices = get_model_bounding_box_vertices(obj_name)
    if vertices:
        print(f"模型 {obj_name} 的最小外接立方体顶点:")
        for i, v in enumerate(vertices):
            print(f"  顶点 {i}: ({v[0]:.4f}, {v[1]:.4f}, {v[2]:.4f})")


def draw_cube_from_vertices(vertices, obj_name="BoundingCube"):
    """
    根据八个顶点坐标绘制立方体
    
    参数:
        vertices: 包含8个顶点坐标的列表，每个顶点是mathutils.Vector或三元组(x,y,z)
        obj_name: 生成的立方体对象名称
    """
    # 确保顶点数量正确
    if len(vertices) != 8:
        print(f"❌ 顶点数量错误，需要8个顶点，实际提供了{len(vertices)}个")
        return None
    
    # 定义立方体的边（连接哪些顶点）
    edges = [
        (0, 1), (1, 2), (2, 3), (3, 0),  # 底面
        (4, 5), (5, 6), (6, 7), (7, 4),  # 顶面
        (0, 4), (1, 5), (2, 6), (3, 7)   # 侧面连接
    ]
    
    # 创建一个新的网格对象
    mesh = bpy.data.meshes.new(name=obj_name)
    mesh.from_pydata(vertices, edges, [])
    mesh.update()
    
    # 创建一个新的物体
    cube_obj = bpy.data.objects.new(obj_name, mesh)
    bpy.context.collection.objects.link(cube_obj)
    
    # 设置红色材质
    material = bpy.data.materials.new(name=f"{obj_name}_Material")
    material.use_nodes = True
    bsdf = material.node_tree.nodes["Principled BSDF"]
    bsdf.inputs['Base Color'].default_value = (255, 0, 0, 1)  # 红色
    bsdf.inputs['Alpha'].default_value = 1.0  # 不透明
    
    # 应用材质
    if cube_obj.data.materials:
        cube_obj.data.materials[0] = material
    else:
        cube_obj.data.materials.append(material)
    
    # 设置为线框模式
    cube_obj.display_type = 'WIRE'
    
    # 使立方体不可选择
    cube_obj.hide_select = True
    
    return cube_obj