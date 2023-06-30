extends CharacterBody2D


const SPEED = 300.0

var _projectile_scene = preload("res://scenes/bullet.tscn")
#var _explosion_scene = preload("res://scenes/explosions.tscn")
const PROYECTIL = preload("res://scenes/bullet.tscn")

func _physics_process(delta):

	var direction = Input.get_vector("move_left", "move_right", "move_down", "move_up"
	)
	if direction.x:
		velocity.x = direction.x * SPEED
	else:
		velocity.x = move_toward(velocity.x, 0, SPEED)
	if direction.y:
		velocity.y = -direction.y * SPEED
	else:
		velocity.y = move_toward(velocity.y, 0, SPEED)

	move_and_slide()
	
	if Input.is_action_just_pressed("shoot"):
		_spawn_projectile()

	
func _spawn_projectile():
	var direction = Vector2.RIGHT
	var projectile = _projectile_scene.instantiate()
	projectile.velocity = direction
	projectile.position = position
	get_parent().add_child(projectile)

