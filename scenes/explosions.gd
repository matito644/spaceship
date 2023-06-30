extends CPUParticles2D


# Called when the node enters the scene tree for the first time.
func _ready():
	emitting = true
	
func _process(delta):
	if !emitting:
		queue_free()
		
