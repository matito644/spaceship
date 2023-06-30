extends Area2D

const speed = 500
var velocity := Vector2.RIGHT
@onready var visible_on_screen_notifier_2d = $VisibleOnScreenNotifier2D

func _ready():
	top_level = true
	velocity = velocity.normalized()
	look_at(velocity+global_position)

func _process(delta):
	position += velocity * speed * delta

func _on_body_entered(body):
	queue_free()

func _on_visible_on_screen_notifier_2d_screen_exited():
	queue_free()
