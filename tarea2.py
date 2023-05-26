# Matias Rivera Contreras

import pyglet
import sys
import os.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
import libs.shaders as sh
import libs.transformations as tr
from OpenGL.GL import *
from libs.gpu_shape import createGPUShape
from libs.obj_handler import read_OBJ
from libs.scene_graph import SceneGraphNode, drawSceneGraphNode, findNode
from libs.assets_path import getAssetPath

# obtener el path a los assets
ASSETS = {
    "base": getAssetPath("superficie.obj"),
    "dona": getAssetPath("dona.obj"),
    "portal": getAssetPath("portal.obj"),
    "muro": getAssetPath("muro.obj"),
    "cuerpo": getAssetPath("cuerpo.obj"),
    "propulsores": getAssetPath("propulsores.obj"),
    "armas": getAssetPath("armas.obj"),
}

# grafo de escena
def createScene(pipeline):
    # creamos los gpu shape a partir de los .obj
    cuerpo = createGPUShape(pipeline, read_OBJ(ASSETS["cuerpo"], (1.0, 0.0, 0.0)))
    propulsores = createGPUShape(pipeline, read_OBJ(ASSETS["propulsores"], (0.0, 0.0, 1.0)))
    armas = createGPUShape(pipeline, read_OBJ(ASSETS["armas"], (0.6, 0.2, 0.8)))
    superficie = createGPUShape(pipeline, read_OBJ(ASSETS["base"], (0.9, 0.6, 0.2)))
    dona = createGPUShape(pipeline, read_OBJ(ASSETS["dona"], (1.0, 0.5, 0.5)))
    portal = createGPUShape(pipeline, read_OBJ(ASSETS["portal"], (0.24, 0.59, 0.31)))
    muro = createGPUShape(pipeline, read_OBJ(ASSETS["muro"], (0.5, 0.52, 0.52)))

    # juntar las tres partes de la nave
    shipNode = SceneGraphNode("shipNode")
    shipNode.childs += [cuerpo, propulsores, armas]

    # nave principal
    mainShipNode = SceneGraphNode("mainShip")
    mainShipNode.transform = tr.uniformScale(0.4)
    mainShipNode.childs += [shipNode]

    # nave de la izquieda
    leftShipNode = SceneGraphNode("leftShip")
    leftShipNode.transform = tr.matmul(
        [
            tr.translate(-0.75, 0, -0.75),
            tr.uniformScale(0.2),
        ]
    )
    leftShipNode.childs += [shipNode]

    # nave de la derecha
    rightShipNode = SceneGraphNode("rightShip")
    rightShipNode.transform = tr.matmul(
        [
            tr.translate(-0.75, 0, 0.75),
            tr.uniformScale(0.2),
        ]
    )
    rightShipNode.childs += [shipNode]

    # flota de naves
    fleetNode = SceneGraphNode("fleet")
    fleetNode.childs += [mainShipNode, leftShipNode, rightShipNode]

    # superficie sobre la que posicionar todo
    baseNode = SceneGraphNode("base")
    baseNode.transform = tr.uniformScale(2)
    baseNode.childs += [superficie]

    # para hacer acrobacias -> una linda dona
    donaNode = SceneGraphNode("dona")
    donaNode.transform = tr.matmul(
        [
            tr.translate(0, 5, 0),
            tr.uniformScale(1.8)
        ]
    )
    donaNode.childs += [dona]

    # para hacer que se esté moviendo luego
    donaRotationNode = SceneGraphNode("donaRotation")
    donaRotationNode.childs += [donaNode]

    # portal 1
    portal1Node = SceneGraphNode("portal1")
    portal1Node.transform = tr.matmul(
        [
            tr.translate(-8, 1, -3),
            tr.uniformScale(1.3)
        ]
    )
    portal1Node.childs += [portal]

    # portal 2
    portal2Node = SceneGraphNode("portal2")
    portal2Node.transform = tr.matmul(
        [
            tr.translate(4, 1, 3),
            tr.uniformScale(1.3)
        ]
    )
    portal2Node.childs += [portal]

    # portales
    portalesNode = SceneGraphNode("portales")
    portalesNode.childs += [portal1Node, portal2Node]

    # muro 1
    muro1Node = SceneGraphNode("muro1")
    muro1Node.transform = tr.matmul(
        [   
            tr.translate(-2, 1, 0),
            tr.scale(1, 1.3, 1),
        ]
    )
    muro1Node.childs += [muro]

    # muro 2
    muro2Node = SceneGraphNode("muro2")
    muro2Node.transform = tr.matmul(
        [   
            tr.translate(-7, 1, 0),
            tr.scale(1, 1.3, 1),
        ]
    )
    muro2Node.childs += [muro]

    # muros
    murosNode = SceneGraphNode("muros")
    murosNode.childs += [muro1Node, muro2Node]

    # nodo de la escena completa
    sceneNode = SceneGraphNode("scene")
    sceneNode.childs += [murosNode, portalesNode, donaRotationNode, baseNode, fleetNode]

    return sceneNode

# controlador
class Controller(pyglet.window.Window):

    def __init__(self, width, height, title="Nave"):
        super().__init__(width, height, title)
        self.total_time = 0.0
        self.pipeline = sh.SimpleModelViewProjectionShaderProgram()
        self.fillPolygon = True
        # crear la escena
        self.scene = createScene(self.pipeline)

# nave
class Nave():
    def __init__(self):
        # parámetros para decir si se está moviendo hacia adelante o rotando
        # partes en cero, es decir, la nave parte quieta
        self.adelante = 0
        self.rotarY = 0
        self.rotarZ = 0

        # velocidad de rotación y de desplazamiento
        self.velocidadRotacion = np.pi*0.01
        self.velocidadAdelante = 0.1

        # al inicio parten acá
        self.x = -8
        self.y = 2
        self.z = 1
        self.rotationYlocal = 0
        self.rotationZlocal = 0
    
    # actualizar x, y, z, además de los dos ángulos para rotar la nave
    def udpate(self):
        self.x += self.velocidadAdelante * self.adelante * np.cos(self.rotationYlocal) * np.cos(self.rotationZlocal)
        self.y += self.velocidadAdelante * self.adelante * np.sin(self.rotationZlocal)
        self.z += self.velocidadAdelante * self.adelante * -np.sin(self.rotationYlocal) * np.cos(self.rotationZlocal)
        self.rotationYlocal -= self.velocidadRotacion * self.rotarY
        self.rotationZlocal += self.velocidadRotacion * 0.5 * self.rotarZ

# instanciar la nave
nave = Nave()

# para manejar la cámaraa
class Camera:
    def __init__(self, eye=np.array([1.0, 1.0, 1.0])):
        self.eye = eye

    # modificar las parámetros que definen self.eye
    def update(self):
        xLejos = 12
        yLejos = -12
        zLejos = -12
        # va a ser la posición de la nave menos las coordenadas escritas antes
        self.eye = np.array([nave.x - xLejos, nave.y - yLejos, nave.z - zLejos])

# instanciar la cámara
camera = Camera()

# definir el tamaño de la ventana
controller = Controller(width=1200, height=800)

# color de la pantalla
glClearColor(0.9, 0.9, 0.9, 1.0)

# test de profundidad
glEnable(GL_DEPTH_TEST)

glUseProgram(controller.pipeline.shaderProgram)

# cuando se presionan dichas teclas
@controller.event
def on_key_press(symbol, modifiers):
    if symbol == pyglet.window.key.SPACE:
        controller.fillPolygon = not controller.fillPolygon
    if symbol == pyglet.window.key.ESCAPE:
        controller.close()
    # permitir el movimiento
    if symbol == pyglet.window.key.W:
        nave.adelante = 1
    if symbol == pyglet.window.key.S:
        nave.adelante = -1
    # permitir rotar
    if symbol == pyglet.window.key.A:
        nave.rotarY = -1
    if symbol == pyglet.window.key.D:
        nave.rotarY = 1
    
# cuando se dejan de presionar dichas teclas
@controller.event
def on_key_release(symbol, modifiers):
    # bloquear el movimiento
    if symbol == pyglet.window.key.W:
        nave.adelante = 0
    if symbol == pyglet.window.key.S:
        nave.adelante = 0
    # bloquear la rotación
    if symbol == pyglet.window.key.A:
        nave.rotarY = 0
    if symbol == pyglet.window.key.D:
        nave.rotarY = 0

# efectuar las rotaciones y la traslación de la nave
def moveFleet(dt):
    fleet = findNode(controller.scene, "fleet")
    fleet.transform = tr.matmul(
        [
            tr.translate(nave.x, nave.y, nave.z),
            tr.rotationY(nave.rotationYlocal),
            tr.rotationZ(nave.rotationZlocal)
        ]
    )

# detectar el mouse en la pantalla
# cabe destacar que como la ventana es de 1200x800, si el mouse está de la mitad de
# la ventana hacia arriba, la nave sube, de lo contrario baja
@controller.event
def on_mouse_motion(x, y, dx, dy):
    if y>400:
         nave.rotarZ = 1
    else:
        nave.rotarZ = -1
    
# dibujar
@controller.event
def on_draw():
    controller.clear()

    camera.update()

    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    if (controller.fillPolygon):
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
    else:
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)    

    # proyección ortográfica
    projection = tr.ortho(-14, 14, -9, 13, 0.1, 100)
    # vista de la cámara
    view = tr.lookAt(
        camera.eye,
        # mirar hacia la nave
        np.array([nave.x, nave.y, nave.z]),
        np.array([0, 1, 0])
    )

    # usar la vista y proyección definida
    glUniformMatrix4fv(glGetUniformLocation(controller.pipeline.shaderProgram, "model"), 1, GL_TRUE, tr.identity())
    glUniformMatrix4fv(glGetUniformLocation(controller.pipeline.shaderProgram, "projection"), 1, GL_TRUE, projection)
    glUniformMatrix4fv(glGetUniformLocation(controller.pipeline.shaderProgram, "view"), 1, GL_TRUE, view)

    # actualizar los parámetros que se encargan de mover la nave (x, y, z, rotaciones)
    nave.udpate()
    # dibujar la escena
    drawSceneGraphNode(controller.scene, controller.pipeline, "model")

# mover objetos
def update(dt, controller):
    controller.total_time += dt

    # mover la dona
    donaRotation = findNode(controller.scene, "donaRotation")
    donaRotation.transform = tr.rotationY(controller.total_time)

    # mover los muros
    muros = findNode(controller.scene, "muros")
    muros.transform = tr.translate(0, 0, 1-np.sin(controller.total_time)*5)

if __name__ == '__main__':
    # ejecutar el movimiento de los objetos de la escena
    pyglet.clock.schedule(update, controller)
    # actualizar la posición de la nave
    pyglet.clock.schedule_interval(moveFleet, 1 / 60)

    pyglet.app.run()
