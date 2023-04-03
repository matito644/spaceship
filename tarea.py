#Matias Rivera Contreras

import pyglet
from pyglet_basic_shapes_wrapper import CustomShape2D
import random
from OpenGL.GL import *


class Controller(pyglet.window.Window):

    def __init__(self, width, height, title="Pyglet window"):
        super().__init__(width, height, title)
        self.total_time = 0.0
        self.fillPolygon = True


# We will use the global controller as communication with the callback function
WIDTH, HEIGHT = 1280, 800
controller = Controller(width=WIDTH, height=HEIGHT)

# Fondo negro
pyglet.gl.glClearColor(0.0, 0.0, 0.0, 1.0)


# Definimos los vértices de nuestra nave
spaceship_vertices = [
    -5, -4, 0.0, 0.0, 1.0,
    -2, -1, 0.0, 0.0, 1.0,
    -3, 0, 0.0, 0.0, 1.0,
    5, -4, 0.0, 0.0, 1.0,
    3, 0, 0.0, 0.0, 1.0,
    2, -1, 0.0, 0.0, 1.0,
    0, -3, 1.0, 0.0, 0.0,
    0, 5, 1.0, 0.0, 0.0,
    -2, -1, 1.0, 0.0, 0.0,
    2, -1, 1.0, 0.0, 0.0,
    -3, -3, 0.6, 0.2, 0.8,
    -1, 0, 0.6, 0.2, 0.8,
    -2, 2, 0.6, 0.2, 0.8,
    3, -3, 0.6, 0.2, 0.8,
    2, 2, 0.6, 0.2, 0.8,
    1, 0, 0.6, 0.2, 0.8,
]

# Defnimos cómo formar los triángulos.
ship_vertices = [
    0, 1, 2,
    3, 4, 5, 
    6, 7, 8,
    6, 7, 9,
    10, 11, 12,
    13, 14, 15,
]

# Definimos los vértices para las estrellas
white_star_vertices = [
    5, 0, 1.0, 1.0, 1.0,
    15, 5, 1.0, 1.0, 1.0,
    5, 5, 1.0, 1.0, 1.0,
    0, 15, 1.0, 1.0, 1.0,
    -5, 5, 1.0, 1.0, 1.0,
    -15, 5, 1.0, 1.0, 1.0,
    -5, 0, 1.0, 1.0, 1.0,
    -10, -10, 1.0, 1.0, 1.0,
    0, -5, 1.0, 1.0, 1.0,
    10, -10, 1.0, 1.0, 1.0,
]

# Seteamos cómo se forman los triángulos.
star_vertices = [
    0, 1, 2,
    2, 3, 4,
    4, 5, 6,
    6, 7, 8,
    8, 9, 0,
    0, 2, 4,
    0, 4, 6,
    0, 6, 8,
]

# Acá se guardarán las naves
batch = pyglet.graphics.Batch()

# Creamos la nave principal
shape_main_ship = CustomShape2D(
    vertices=spaceship_vertices,
    indices=ship_vertices,
    batch=batch,
)
# Elegimos posición inicial y escala
shape_main_ship.position = (WIDTH * 0.5, 150.0)
shape_main_ship.scale = 15

# Creamos la nave de la izquierda
shape_left_ship = CustomShape2D(
    vertices=spaceship_vertices,
    indices=ship_vertices,
    batch=batch,
)
# Elegimos posición inicial y escala
shape_left_ship.position = (WIDTH * 0.5 - 150, 100.0)
shape_left_ship.scale = 10

# Creamos nave de la derecha
shape_right_ship = CustomShape2D(
    vertices=spaceship_vertices,
    indices=ship_vertices,
    batch=batch,
)
# Elegimos posición inicial y escala
shape_right_ship.position = (WIDTH * 0.5 + 150, 100.0)
shape_right_ship.scale = 10

# What happens when the user presses these keys
@controller.event
def on_key_press(symbol, modifiers):
    if symbol == pyglet.window.key.SPACE:
        controller.fillPolygon = not controller.fillPolygon
    elif symbol == pyglet.window.key.ESCAPE:
        controller.close()

# Acá almacenamos las estrellas
stars = []
def createStars(interval):
    shape_star = CustomShape2D(
    vertices=white_star_vertices,
    indices=star_vertices,
    )
    # Elegimos posición inicial aleatoria
    initial_position = random.randint(0, WIDTH)
    shape_star.position = (initial_position, 820.0)
    stars.append(shape_star)
    print(len(stars))

@controller.event
def on_draw():
    controller.clear()
    if (controller.fillPolygon):
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
    else:
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
    # Dibujando las naves
    for star in stars:
        star.draw()
    # Dibujando las naves
    batch.draw()

# Función para actualizar las posiciones de las figuras
def update_figures(dt):
    # Hacemos que se mueva cada estrella
    for star in stars:
        star.y -= 1
        # Si sale de la pantalla la eliminamos
        if star.y < -10 :
            star.delete()
            stars.remove(star)

# Creamos estrellas cada 0.2 segundos.
pyglet.clock.schedule_interval(createStars, 0.2)

# Actualizamos las figuras cada 0.1 segundos.
pyglet.clock.schedule_interval(update_figures, 0.001)

# Set the view
pyglet.app.run()
