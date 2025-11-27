import pygame
from configuracion import *

class Semaforo:
    def __init__(self, nodo_id, pos, estado_inicial="ROJO", tiempo_cambio=180):
        # El nodo al que pertenece el semaforo
        self.nodo_id = nodo_id
        # Posicion del semaforo
        self.pos = pos
        # En que estado se inicializa (rojo o verde)
        self.estado = estado_inicial
        # Contador para luego ejecutar el cambio
        self.timer = 0
        # Cada cuanto tiempo cambia de estado
        self.tiempo_cambio = tiempo_cambio
    # Actualiza el semaforo entre sus estados segun el tiempo asignado a este 
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