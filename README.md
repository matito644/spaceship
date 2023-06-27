# Tarea 3

Info:

- Logré que se grabaran los puntos de control de manera correcta (se muestra un mensaje en la terminal al presionar la tecla R), también logré que se graficara la curva interpolada (usé Bezier) por la que pasa la nave (tecla V), además de implementar una cámara cercana a la nave (tecla C) y que se haga una pirueta que pasa por el único elemento que conservé de la tarea anterior, una dona (tecla P).

El recorrido funciona tomando 4 puntos de control y genera la curva de Bezier entre esos puntos, si se entregan más de 4 puntos se considera el último punto del tramo anterior como punto inicial y se toman 3 puntos más, si no existen esos 3 puntos se repite el último punto que existe una o dos veces. Las rotaciones se hacen según la posición actual de la nave y la siguiente. Tiene defectos:
- Si se graban más de 4 puntos, el cambio entre los tramos es brusco en las rotaciones.
- Dejé inhabilitada la rotación en el eje z en el recorrido pues no logré controlar que fuera suave y correcta.
- Considerando lo anterior, una curva que se mueve fuera del plano en donde parte la nave no va a tener una orientación correcta.

Consideraciones:
- Decidí sacar los muros y portales pues no afectan el funcionamiento de esta tarea.
- La curva graficada desaparece al terminar el recorrido.
- La nave vuelve a su posición al terminar el recorrido.
- Se piden como mínimo 4 puntos de control para poder generar la curva y empezar el recorrido.
