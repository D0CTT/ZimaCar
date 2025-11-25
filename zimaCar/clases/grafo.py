import pygame
import heapq
from configuracion import *

class Grafo:
    def __init__(self):
        self.nodos = {}  # "A": (x, y)
        self.aristas = {} # "A": {"B": costo}
        self.camino_resaltado = [] 

    def agregar_nodo(self, nombre, pos):
        self.nodos[nombre] = pos
        self.aristas[nombre] = {}

    def conectar(self, nodo_a, nodo_b, costo=1):
        self.aristas[nodo_a][nodo_b] = costo
        self.aristas[nodo_b][nodo_a] = costo

    def eliminar_nodo(self, nombre_nodo):
        if nombre_nodo in self.nodos:
            del self.nodos[nombre_nodo]
        if nombre_nodo in self.aristas:
            del self.aristas[nombre_nodo]
        for otro_nodo, sus_vecinos in self.aristas.items():
            if nombre_nodo in sus_vecinos:
                del sus_vecinos[nombre_nodo]
        self.camino_resaltado = []

    def dijkstra(self, inicio, fin):
        cola_prioridad = [(0, inicio)]
        distancias = {nodo: float('inf') for nodo in self.nodos}
        distancias[inicio] = 0
        padres = {nodo: None for nodo in self.nodos}

        while cola_prioridad:
            distancia_actual, nodo_actual = heapq.heappop(cola_prioridad)

            if nodo_actual == fin:
                break 

            if distancia_actual > distancias[nodo_actual]:
                continue

            for vecino, costo in self.aristas[nodo_actual].items():
                nueva_distancia = distancia_actual + costo
                if nueva_distancia < distancias[vecino]:
                    distancias[vecino] = nueva_distancia
                    padres[vecino] = nodo_actual
                    heapq.heappush(cola_prioridad, (nueva_distancia, vecino))
        
        camino = []
        actual = fin
        while actual is not None:
            camino.insert(0, actual)
            actual = padres[actual]
        
        if len(camino) == 1 and camino[0] != inicio:
            return []
            
        self.camino_resaltado = camino
        return camino

    def dibujar(self, pantalla):
        # 1. Dibujar CALLES (Base ancha para dos carriles)
        ANCHO_CALLE = ANCHO_C  # Espacio para dos autos
        for nodo_a, vecinos in self.aristas.items():
            for nodo_b in vecinos:
                if nodo_a in self.nodos and nodo_b in self.nodos:
                    # Dibujar pavimento
                    pygame.draw.line(pantalla, (80, 80, 80), self.nodos[nodo_a], self.nodos[nodo_b], ANCHO_CALLE)
                    # Dibujar linea divisoria (Amarilla fina)
                    pygame.draw.line(pantalla, (255, 200, 0), self.nodos[nodo_a], self.nodos[nodo_b], 2)

        # 2. Dibujar camino resaltado (Ruta del GPS)
        if len(self.camino_resaltado) > 1:
            for i in range(len(self.camino_resaltado) - 1):
                na = self.camino_resaltado[i]
                nb = self.camino_resaltado[i+1]
                if na in self.nodos and nb in self.nodos:
                    pass 

        # 3. Dibujar NODOS COMO CUADRADOS
        lado = RADIO_NODO * 2 # El tamaño total es el diámetro

        for nombre, pos in self.nodos.items():
            color = VERDE if nombre in self.camino_resaltado else AZUL
            
            # Crear el rectángulo centrado: (x - radio, y - radio, ancho, alto)
            rect_nodo = pygame.Rect(pos[0] - RADIO_NODO, pos[1] - RADIO_NODO, lado, lado)
            
            # Dibujar el cuadrado relleno
            pygame.draw.rect(pantalla, color, rect_nodo)
            
            # Dibujar un borde blanco (opcional, por estética)
            pygame.draw.rect(pantalla, BLANCO, rect_nodo, 2)
            
            # Texto centrado
            fuente = pygame.font.SysFont("Arial", 12)
            texto = fuente.render(nombre, True, BLANCO)
            rect_texto = texto.get_rect(center=pos) # Centrar texto matemáticamente en el nodo
            pantalla.blit(texto, rect_texto)