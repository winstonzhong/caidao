import json

'''
[gd_resource type="Resource" script_class="Item" load_steps=3 format=3 uid="uid://c02b0jq5bdpkm"]

[ext_resource type="Script" uid="uid://d3wghc3nqady6" path="res://Test3/item.gd" id="1_tv0u3"]
[ext_resource type="Texture2D" uid="uid://dxaf2xl7ac6c7" path="res://Test3/textures/sword.png" id="2_wf8fi"]

[resource]
script = ExtResource("1_tv0u3")
name = "Sword"
id = "sword"
texture = ExtResource("2_wf8fi")
recipe = Array[String](["pickaxe", "", "", "", "", "", "", "", ""])
'''


def 打包资源():
    d = {
        "name": "Sword",
        "id": "sword",
        "texture": "/home/yka-003/inventory-example/Test3/textures/sword.png",
        "recipe": ["pickaxe", "", "", "", "", "", "", "", ""],
    }