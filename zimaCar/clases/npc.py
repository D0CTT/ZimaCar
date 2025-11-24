import pygame
import math
from configuracion import *

class AutoNPC:
    def __init__(self, id, ruta_patrulla, mapa_nodos):
        """
        ruta_patrulla: Lista de nombres de nodos ej: ['B', 'C']
        El auto irá de B a C, y luego de C a B infinitamente.
        """
        self.id = id
        self.color = (255, 165, 0) # Naranja (Taxi)
        self.velocidad = 1.5 # Un poco más lento que el tuyo
        self.mapa_nodos = mapa_nodos
        
        # Configuración de ruta
        self.ruta_base = ruta_patrulla
        self.indice_actual = 0
        self.direccion_avance = 1 # 1 para ir adelante, -1 para volver
        
        # Posición inicial
        nodo_inicio = self.ruta_base[0]
        self.pos = list(mapa_nodos[nodo_inicio]) # Copia de coordenadas
        
        # Objetivo inicial
        self.actualizar_objetivo()

    def actualizar_objetivo(self):
        # Determinar el siguiente nodo en la lista
        siguiente_indice = self.indice_actual + self.direccion_avance
        
        # Si llegamos al final o al inicio de la lista, invertimos dirección
        if siguiente_indice >= len(self.ruta_base) or siguiente_indice < 0:
            self.direccion_avance *= -1
            siguiente_indice = self.indice_actual + self.direccion_avance
            
        self.indice_actual = siguiente_indice
        nombre_obj = self.ruta_base[self.indice_actual]
        self.pos_objetivo = self.mapa_nodos[nombre_obj]

    def update(self):
        # Movimiento simple hacia el objetivo
        dir_x = self.pos_objetivo[0] - self.pos[0]
        dir_y = self.pos_objetivo[1] - self.pos[1]
        dist = math.hypot(dir_x, dir_y)
        
        if dist <= self.velocidad:
            self.pos = list(self.pos_objetivo)
            self.actualizar_objetivo() # Cambiar meta
        else:
            dir_x /= dist
            dir_y /= dist
            self.pos[0] += dir_x * self.velocidad
            self.pos[1] += dir_y * self.velocidad

    def dibujar(self, pantalla):
        pygame.draw.circle(pantalla, self.color, (int(self.pos[0]), int(self.pos[1])), 15)
        # Borde negro para distinguirlo
        pygame.draw.circle(pantalla, NEGRO, (int(self.pos[0]), int(self.pos[1])), 15, 2)