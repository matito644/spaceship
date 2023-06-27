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
from libs.shapes import Shape

# funciones para generar las curvas de bezier
def generateT(t):
    return np.array([[1, t, t**2, t**3]]).T

def bezierMatrix(P0, P1, P2, P3):
    G = np.concatenate((P0, P1, P2, P3), axis=1)
    Mb = np.array([[1, -3, 3, -1], [0, 3, -6, 3], [0, 0, 3, -3], [0, 0, 0, 1]])
    return np.matmul(G, Mb)

def evalCurve(M, N):
    ts = np.linspace(0.0, 1.0, N)
    curve = np.ndarray(shape=(N, 3), dtype=float)
    for i in range(len(ts)):
        T = generateT(ts[i])
        curve[i, 0:3] = np.matmul(M, T).T
    return curve


# obtener el path a los assets
ASSETS = {
    "base": getAssetPath("superficie.obj"),
    "dona": getAssetPath("dona.obj"),
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

    # nodo de la escena completa
    sceneNode = SceneGraphNode("scene")
    sceneNode.childs += [donaRotationNode, baseNode, fleetNode]

    return sceneNode

# controlador
class Controller(pyglet.window.Window):

    def __init__(self, width, height, title="Nave"):
        super().__init__(width, height, title)
        self.total_time = 0.0
        self.pipeline = sh.SimpleModelViewProjectionShaderProgram()
        self.fillPolygon = True
        self.reallyUsed = 500
        # tiempo de animación
        self.step = 0
        # curva de bezier
        self.curve = None
        # indica si se puede ver la curva
        self.seeCurve = -1
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

        # indica si la nave se puede mover
        self.able = 1
        # indica si la nave está en una pirueta
        self.loop = 0
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
        # solo cuando la nave no esté recorriendo una curva
        if self.able == 1:
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
        self.c = -1

    # modificar las parámetros que definen self.eye
    def update(self):
        # cámara normal
        if self.c == -1:
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

# acá se almacenarán los puntos agregados
listOfPoints = []
# cuando se presionan dichas teclas
@controller.event
def on_key_press(symbol, modifiers):
    if nave.able == 1:
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
        # registrar los puntos
        if symbol == pyglet.window.key.R:
            info = [nave.x, nave.y, nave.z, nave.rotationYlocal, nave.rotationZlocal]
            listOfPoints.append(info)
            print("Punto agregado!")
            print("     Pos en x: " + str(listOfPoints[-1][0]))
            print("     Pos en y: " + str(listOfPoints[-1][1]))
            print("     Pos en z: " + str(listOfPoints[-1][2]))
            print("Total de puntos: " + str(len(listOfPoints)))
    if symbol == pyglet.window.key._1:
        # no basta un solo punto para generar la curva
        if len(listOfPoints) > 3:
            # if len(listOfPoints)%3 == 1 or len(listOfPoints) == 4:
            # generar la curva
            controller.curve = goBezier()
            # la nave no se puede mover con WASD mientras recorre la curva
            nave.able = 0
            # else:
            #     print("Por favor añade otro punto de control")
        else:
            print("Por favor añade otro punto de control")
    # cambiar a una cámara en tercera persona
    if symbol == pyglet.window.key.C:
        camera.c = -camera.c
    # iniciar la pirueta
    if symbol == pyglet.window.key.P:
        # la nave no se puede mover con WASD mientras realiza la pirueta
        nave.able = 0
        nave.loop = 1
    # visualizar la curva
    if symbol == pyglet.window.key.V:
        if controller.seeCurve == 1:
            controller.seeCurve = -1
        # mismas condiciones cuando se apreta 1 o cuando se quiere ver la curva, que aún no se genera
        elif len(listOfPoints) > 3:
            # if len(listOfPoints)%3 == 1 or len(listOfPoints) == 4:
            # generar la curva
            controller.curve = goBezier()
            controller.seeCurve = 1
        # si estamos en el loop se puede activar también
        elif nave.loop == 1:
            controller.seeCurve = -controller.seeCurve
        else:
            print("Aún no se genera la curva")

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

    # proyección en perspectiva
    projection = tr.perspective(60, 1200/800, 0.1, 100)
    # cámara normal
    if camera.c == -1:
        view = tr.lookAt(
            camera.eye,
            # mirar hacia la nave
            np.array([nave.x, nave.y+1, nave.z]),
            np.array([0, 1, 0])
        )
    else: # ajustar la posición y orientación de la cámara en tercera persona
        fleet_position = np.array([nave.x, nave.y, nave.z, 1])
        # decidí que la cámara no siguiera la rotación en el eje z pues se ve mejor
        camera_transform = tr.matmul(
            [
                tr.rotationY(nave.rotationYlocal),
                #tr.rotationZ(nave.rotationZlocal),
                tr.translate(-3, 3, 0),
                #tr.rotationZ(-nave.rotationZlocal),
                tr.rotationY(-nave.rotationYlocal),
            ]
        )
        look_at_transform = tr.matmul(
            [
                tr.rotationY(nave.rotationYlocal),
                #tr.rotationZ(nave.rotationZlocal),
                tr.translate(3, -1, 0),
                #tr.rotationZ(-nave.rotationZlocal),
                tr.rotationY(-nave.rotationYlocal),
            ]
        )
        # considerar la posición de la nave
        camera_position = np.matmul(camera_transform, fleet_position)
        look_at_position = np.matmul(look_at_transform, fleet_position)

        view = tr.lookAt(camera_position[0:3], look_at_position[0:3], np.array([0, 1, 0])
    )

    # usar la vista y proyección definida
    glUniformMatrix4fv(glGetUniformLocation(controller.pipeline.shaderProgram, "model"), 1, GL_TRUE, tr.identity())
    glUniformMatrix4fv(glGetUniformLocation(controller.pipeline.shaderProgram, "projection"), 1, GL_TRUE, projection)
    glUniformMatrix4fv(glGetUniformLocation(controller.pipeline.shaderProgram, "view"), 1, GL_TRUE, view)

    # actualizar los parámetros que se encargan de mover la nave (x, y, z, rotaciones)
    nave.udpate()
    # visualizar la curva generada por los puntos de control
    if controller.seeCurve == 1 and nave.loop != 1:
            curve = drawCurve(controller.curve)
            gpuCurve = sh.GPUShape().initBuffers()
            pipelineLines.setupVAO(gpuCurve)
            gpuCurve.fillBuffers(curve.vertices, curve.indices, GL_STATIC_DRAW)
            glUseProgram(pipelineLines.shaderProgram)
            glUniformMatrix4fv(glGetUniformLocation(pipelineLines.shaderProgram, "model"), 1, GL_TRUE, tr.identity())
            glUniformMatrix4fv(glGetUniformLocation(pipelineLines.shaderProgram, "projection"), 1, GL_TRUE, projection)
            glUniformMatrix4fv(glGetUniformLocation(pipelineLines.shaderProgram, "view"), 1, GL_TRUE, view)
            pipelineLines.drawCall(gpuCurve, GL_LINES)
    # mover la nave según la curva de bezier dada por los puntos de control
    if nave.able == 0 and nave.loop == 0:
        # Agregamos los step para tener la cuena de las iteraciones
        # Si step es mayor al número de puntos, reseteamos su cuenta
        if controller.step >= controller.reallyUsed-1:
            controller.step = 0
            # la nave se puede mover
            nave.able = 1
            # la lista queda vacía al terminar
            listOfPoints.clear()
            print("Travesía completada!")
            controller.seeCurve = -1
        # definir el ángulo de rotación según dos posiciones de la curva interpolada
        angleY = np.arctan2(controller.curve[controller.step+1, 0] - controller.curve[controller.step, 0], controller.curve[controller.step+1, 2] - controller.curve[controller.step, 2])
        # angleZ = np.arctan2(controller.curve[controller.step+1, 0] - controller.curve[controller.step, 0], controller.curve[controller.step+1, 1] - controller.curve[controller.step, 1])
        if controller.curve.all() != None and controller.step%200 != 199:
            # mover la nave según la curva
            nave.x = controller.curve[controller.step, 0]
            nave.y = controller.curve[controller.step, 1]
            nave.z = controller.curve[controller.step, 2]
            # rotar
            nave.rotationYlocal = angleY-np.pi/2
            # nave.rotationZlocal = angleZ+np.pi/2
            nave.rotationZlocal = 0
        # aumentar el step
        controller.step += 1

    # ejecutar el loop definido
    if nave.loop == 1:
        # cuando termina:
        if controller.step >= 800:
            controller.step = 0
            nave.loop = 0
            nave.able = 1
            print("Pirueta completada!")
            # desaparece una vez se termina de recorrer
            controller.seeCurve = -1

        # casos borde en las rotaciones ocurren cuando np.arctan2 se ejecuta con los mismos puntos
        if controller.step%200 != 199:
            # definir el ángulo de rotación según dos posiciones de la curva interpolada
            angleY = np.arctan2(bezierCurveLoop[controller.step+1, 0] - bezierCurveLoop[controller.step, 0], bezierCurveLoop[controller.step+1, 2] - bezierCurveLoop[controller.step, 2])
            # mover la nave y hacerla rotar
            nave.x = bezierCurveLoop[controller.step, 0]
            nave.y = bezierCurveLoop[controller.step, 1]
            nave.z = bezierCurveLoop[controller.step, 2]
            nave.rotationYlocal = angleY - np.pi/2
            nave.rotationZlocal = 0
        # graficar la línea de la pirueta
        if controller.seeCurve == 1:
            curve = drawCurve(bezierCurveLoop)
            gpuCurve = sh.GPUShape().initBuffers()
            pipelineLines.setupVAO(gpuCurve)
            gpuCurve.fillBuffers(curve.vertices, curve.indices, GL_STATIC_DRAW)
            glUseProgram(pipelineLines.shaderProgram)
            glUniformMatrix4fv(glGetUniformLocation(pipelineLines.shaderProgram, "model"), 1, GL_TRUE, tr.identity())
            glUniformMatrix4fv(glGetUniformLocation(pipelineLines.shaderProgram, "projection"), 1, GL_TRUE, projection)
            glUniformMatrix4fv(glGetUniformLocation(pipelineLines.shaderProgram, "view"), 1, GL_TRUE, view)
            pipelineLines.drawCall(gpuCurve, GL_LINES)
        # aumentar el step
        controller.step += 1

    # volver al pipeline para el resto de figuras
    glUseProgram(controller.pipeline.shaderProgram)
    # dibujar la escena
    drawSceneGraphNode(controller.scene, controller.pipeline, "model")


# Si se hubiera querido que la velocidad fuese la misma siempre, habría que haber
# elegido un N proporcional a la distancia entre los puntos de la grabación para usar en la función evalCurve(M, N),
# de tal modo que si la distancia fuese mayor, mayor fuese el N, pero como nosotros elegimos la velocidad,
# decidí que no fuera constante para cada tramo de la ruta
# función para generar la curva
def goBezier():
    points = len(listOfPoints)
    index = 0
    # los primeros cuatro puntos:
    P0 = np.array([[listOfPoints[index][0], listOfPoints[index][1], listOfPoints[index][2]]]).T
    P1 = np.array([[listOfPoints[index+1][0], listOfPoints[index+1][1], listOfPoints[index+1][2]]]).T
    P2 = np.array([[listOfPoints[index+2][0], listOfPoints[index+2][1], listOfPoints[index+2][2]]]).T
    P3 = np.array([[listOfPoints[index+3][0], listOfPoints[index+3][1], listOfPoints[index+3][2]]]).T
    index+=3
    indexForNumberOfPoints = 1
    M = bezierMatrix(P0, P1, P2, P3)
    # la nave pasa por 200 puntos en cada tramo (cada 4 puntos)
    bezierCurve = evalCurve(M, 200)
    BezierCurve = bezierCurve
    # utilizando el último punto de la curva anterior y los siguientes tres puntos
    while index+3 < points:
        P0 = np.array([[listOfPoints[index][0], listOfPoints[index][1], listOfPoints[index][2]]]).T
        P1 = np.array([[listOfPoints[index+1][0], listOfPoints[index+1][1], listOfPoints[index+1][2]]]).T
        P2 = np.array([[listOfPoints[index+2][0], listOfPoints[index+2][1], listOfPoints[index+2][2]]]).T
        P3 = np.array([[listOfPoints[index+3][0], listOfPoints[index+3][1], listOfPoints[index+3][2]]]).T
        index+=3
        indexForNumberOfPoints+=1
        M1 = bezierMatrix(P0, P1, P2, P3)
        bezierCurve1 = evalCurve(M1, 200)
        # concatenar las curvas
        BezierCurve = np.concatenate((BezierCurve, bezierCurve1), axis=0)
    # caso en que no existían 3 puntos más
    if points > 4 and index != points-1:
        if points-index == 2:
            P0 = np.array([[listOfPoints[index][0], listOfPoints[index][1], listOfPoints[index][2]]]).T
            P1 = np.array([[listOfPoints[index+1][0], listOfPoints[index+1][1], listOfPoints[index+1][2]]]).T
            M2 = bezierMatrix(P0, P1, P1, P1)
            bezierCurve2 = evalCurve(M2, 200)
            indexForNumberOfPoints+=1
            BezierCurve = np.concatenate((BezierCurve, bezierCurve2), axis=0)
        elif points-index == 3:
            P0 = np.array([[listOfPoints[index][0], listOfPoints[index][1], listOfPoints[index][2]]]).T
            P1 = np.array([[listOfPoints[index+1][0], listOfPoints[index+1][1], listOfPoints[index+1][2]]]).T
            P2 = np.array([[listOfPoints[index+2][0], listOfPoints[index+2][1], listOfPoints[index+2][2]]]).T
            M2 = bezierMatrix(P0, P1, P2, P2)
            bezierCurve2 = evalCurve(M2, 200)
            indexForNumberOfPoints+=1
            BezierCurve = np.concatenate((BezierCurve, bezierCurve2), axis=0)
    # ajustar la cantidad de puntos por los que se mueve (efectivamente pasa) la nave
    controller.reallyUsed = indexForNumberOfPoints*200
    return BezierCurve

# función para poder obtener la curva que se grafica
def drawCurve(curve):
    # formar cada vértice según las posiciones dadas por la curva
    vertex1 = [curve[0, 0], curve[0, 1], curve[0, 2],  0, 0, 0]
    for i in range(1, len(curve)):
        ivertex = [curve[i, 0], curve[i, 1], curve[i, 2],  0, 0, 0]
        if i == 1:
            vertices = np.concatenate((vertex1, ivertex), axis=0)
        else:
            vertices = np.concatenate((vertices, ivertex), axis=0)
    indices = [0]
    # iterar formando pares del estilo 1,2; 2,3; 3,4 ...
    for i in range(1, len(curve)):
        indices += ([i] * 2)
    return Shape(vertices, indices)

if __name__ == '__main__':
    # pipeline para dibujar líneas
    pipelineLines = sh.SimpleShaderProgram()
    # definir la curva para la pirueta, es un 8, dividido en 4 tramos
    P0 = np.array([[0, 5, -5]]).T
    P1 = np.array([[-6, 5, -5]]).T
    P2 = np.array([[-6, 5, 0]]).T
    P3 = np.array([[0, 5, 0]]).T
    MLoop1 = bezierMatrix(P0, P1, P2, P3)
    bezierCurveLoop1 = evalCurve(MLoop1, 200)
    # segundo tramo
    P4 = np.array([[0, 5, 0]]).T
    P5 = np.array([[6, 5, 0]]).T
    P6 = np.array([[6, 5, 5]]).T
    P7 = np.array([[0, 5, 5]]).T
    MLoop2 = bezierMatrix(P4, P5, P6, P7)
    bezierCurveLoop2 = evalCurve(MLoop2, 200)
    # tercer tramo
    P8 = np.array([[0, 5, 5]]).T
    P9 = np.array([[-6, 5, 5]]).T
    P10 = np.array([[-6, 5, 0]]).T
    P11 = np.array([[0, 5, 0]]).T
    MLoop3 = bezierMatrix(P8, P9, P10, P11)
    bezierCurveLoop3 = evalCurve(MLoop3, 200)
    # cuarto tramo
    P12 = np.array([[0, 5, 0]]).T
    P13 = np.array([[6, 5, 0]]).T
    P14 = np.array([[6, 5, -5]]).T
    P15 = np.array([[0, 5, -5]]).T
    MLoop4 = bezierMatrix(P12, P13, P14, P15)
    bezierCurveLoop4 = evalCurve(MLoop4, 200)
    # unir todas las curvas
    bezierCurveLoop = np.concatenate((bezierCurveLoop1, bezierCurveLoop2, bezierCurveLoop3, bezierCurveLoop4), axis=0)
    # actualizar la posición de la nave
    pyglet.clock.schedule_interval(moveFleet, 1 / 60)

    pyglet.app.run()
