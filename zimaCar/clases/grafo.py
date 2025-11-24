import pygame
import heapq # <--- NUEVO: Necesario para el algoritmo
from configuracion import *

class Grafo:
    def __init__(self):
        self.nodos = {} 
        self.aristas = {} 
        self.camino_resaltado = [] # <--- NUEVO: Para guardar la ruta encontrada

    def agregar_nodo(self, nombre, pos):
        self.nodos[nombre] = pos
        self.aristas[nombre] = {}

    def conectar(self, nodo_a, nodo_b, costo=1):
        self.aristas[nodo_a][nodo_b] = costo
        self.aristas[nodo_b][nodo_a] = costo

    # --- NUEVO: ALGORITMO DIJKSTRA ---
    def dijkstra(self, inicio, fin):
        cola_prioridad = [(0, inicio)]
        distancias = {nodo: float('inf') for nodo in self.nodos}
        distancias[inicio] = 0
        padres = {nodo: None for nodo in self.nodos} # Para reconstruir el camino

        while cola_prioridad:
            distancia_actual, nodo_actual = heapq.heappop(cola_prioridad)

            if nodo_actual == fin:
                break # Llegamos al destino

            if distancia_actual > distancias[nodo_actual]:
                continue

            for vecino, costo in self.aristas[nodo_actual].items():
                nueva_distancia = distancia_actual + costo
                if nueva_distancia < distancias[vecino]:
                    distancias[vecino] = nueva_distancia
                    padres[vecino] = nodo_actual
                    heapq.heappush(cola_prioridad, (nueva_distancia, vecino))
        
        # Reconstruir el camino (Backtracking)
        camino = []
        actual = fin
        while actual is not None:
            camino.insert(0, actual) # Insertar al inicio
            actual = padres[actual]
        
        # Si el camino solo tiene 1 nodo y no es el inicio, es que no hay ruta
        if len(camino) == 1 and camino[0] != inicio:
            return []
            
        self.camino_resaltado = camino # Guardamos para dibujar
        return camino

    def dibujar(self, pantalla):
        # 1. Dibujar caminos normales (Gris)
        for nodo_a, vecinos in self.aristas.items():
            for nodo_b in vecinos:
                pygame.draw.line(pantalla, GRIS, self.nodos[nodo_a], self.nodos[nodo_b], 4)

        # 2. NUEVO: Dibujar camino resaltado (Verde)
        if len(self.camino_resaltado) > 1:
            for i in range(len(self.camino_resaltado) - 1):
                nodo_a = self.camino_resaltado[i]
                nodo_b = self.camino_resaltado[i+1]
                pygame.draw.line(pantalla, VERDE, self.nodos[nodo_a], self.nodos[nodo_b], 6)

        # 3. Dibujar nodos
        for nombre, pos in self.nodos.items():
            color = AZUL
            # Si el nodo es parte del camino, pintarlo verde
            if nombre in self.camino_resaltado:
                color = VERDE
            pygame.draw.circle(pantalla, color, pos, RADIO_NODO)
            
            # (Opcional) Dibujar nombre del nodo
            fuente = pygame.font.SysFont("Arial", 16)
            texto = fuente.render(nombre, True, BLANCO)
            pantalla.blit(texto, (pos[0]-5, pos[1]-10))
    
    def eliminar_nodo(self, nombre_nodo):
        # 1. Eliminar el nodo de la lista de coordenadas
        if nombre_nodo in self.nodos:
            del self.nodos[nombre_nodo]
        
        # 2. Eliminar sus conexiones salientes
        if nombre_nodo in self.aristas:
            del self.aristas[nombre_nodo]
            
        # 3. Eliminar sus conexiones entrantes (desde otros vecinos)
        for otro_nodo, sus_vecinos in self.aristas.items():
            if nombre_nodo in sus_vecinos:
                del sus_vecinos[nombre_nodo]
        
        # 4. Limpiar si era parte del camino resaltado
        self.camino_resaltado = []