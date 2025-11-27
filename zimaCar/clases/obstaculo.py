import pygame
from configuracion import *

class Obstaculo:
    def __init__(self, pos):
        # Donde esta el obstaculo
        self.pos = pos
        # Cuanto mide el obstaculo en radio de circulo
        self.radio = 10
    # Dibujar el obstaculo
    def dibujar(self, pantalla):
        pygame.draw.circle(pantalla, (100, 100, 100), self.pos, self.radio)
        pygame.draw.circle(pantalla, (50, 50, 50), self.pos, self.radio, 2)