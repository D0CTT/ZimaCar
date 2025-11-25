import pygame
from configuracion import *

class Obstaculo:
    def __init__(self, pos):
        self.pos = pos
        self.radio = 10
        
    def dibujar(self, pantalla):
        pygame.draw.circle(pantalla, (100, 100, 100), self.pos, self.radio)
        pygame.draw.circle(pantalla, (50, 50, 50), self.pos, self.radio, 2)