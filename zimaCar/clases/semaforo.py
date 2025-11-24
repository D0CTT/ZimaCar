import pygame
from configuracion import *

class Semaforo:
    def __init__(self, nodo_id, pos, estado_inicial="ROJO", tiempo_cambio=180):
        self.nodo_id = nodo_id # En qué nodo está (Ej: "B")
        self.pos = pos         # Coordenadas (x, y)
        self.estado = estado_inicial # "VERDE" o "ROJO"
        self.timer = 0
        self.tiempo_cambio = tiempo_cambio # Frames para cambiar de color
        
    def update(self):
        # Lógica de tiempo
        self.timer += 1
        if self.timer >= self.tiempo_cambio:
            self.timer = 0
            # Cambiar estado
            if self.estado == "ROJO":
                self.estado = "VERDE"
            else:
                self.estado = "ROJO"

    def dibujar(self, pantalla):
        # Dibujamos un pequeño indicador al lado del nodo
        color = ROJO if self.estado == "ROJO" else VERDE
        
        # Offset para que no tape el nodo azul (lo dibujamos un poco arriba y a la derecha)
        pos_dibujo = (self.pos[0] + 15, self.pos[1] - 15)
        
        pygame.draw.circle(pantalla, color, pos_dibujo, 8)
        pygame.draw.circle(pantalla, BLANCO, pos_dibujo, 8, 1) # Borde blanco