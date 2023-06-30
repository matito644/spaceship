extends CharacterBody2D


var _explosion_scene = preload("res://scenes/explosions.tscn")

	
var count = 5
func _on_area_2d_area_entered(area):
	print(count)
	if count == 0:
		var effect := _explosion_scene.instantiate()
		effect.global_position = global_position
		get_tree().current_scene.add_child(effect)
		queue_free()
	else:
		count = count - 1
