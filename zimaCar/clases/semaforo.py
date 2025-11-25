import pygame
from configuracion import *

class Semaforo:
    def __init__(self, nodo_id, pos, estado_inicial="ROJO", tiempo_cambio=180):
        self.nodo_id = nodo_id
        self.pos = pos
        self.estado = estado_inicial
        self.timer = 0
        self.tiempo_cambio = tiempo_cambio
        
    def update(self):
        self.timer += 1
        if self.timer >= self.tiempo_cambio:
            self.timer = 0
            self.estado = "VERDE" if self.estado == "ROJO" else "ROJO"

    def dibujar(self, pantalla):
        color = ROJO if self.estado == "ROJO" else VERDE
        pos_dibujo = (self.pos[0] + 15, self.pos[1] - 15)
        pygame.draw.circle(pantalla, color, pos_dibujo, 8)
        pygame.draw.circle(pantalla, BLANCO, pos_dibujo, 8, 1)