import pygame
import numpy as np
import heapq # Para verificar que tienes la herramienta para Dijkstra

# Inicializar pygame
pygame.init()

# Configurar pantalla
screen = pygame.display.set_mode((400, 300))
pygame.display.set_caption("Simulación Auto - Test")

# Loop principal
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    
    screen.fill((0, 0, 0)) # Fondo negro
    pygame.display.flip()

pygame.quit()
print("¡Todo instalado correctamente!")