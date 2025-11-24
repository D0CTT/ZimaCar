import pygame
import math
from configuracion import *

class Auto:
    def __init__(self, pos_inicial):
        self.pos = list(pos_inicial) # [x, y]
        self.ruta = [] # Lista de NOMBRES de nodos ['A', 'B', 'C']
        self.velocidad = VELOCIDAD_AUTO # Definido en configuracion.py
        self.radio_llegada = 5 # Cuán cerca debe estar para considerar que "llegó"
    
    def planificar_ruta(self, ruta_nombres):
        # Recibimos la lista de nombres ['A', 'B', ...]
        self.ruta = ruta_nombres
        
        # Truco: Si ya estoy en el nodo 'A', lo quito de la lista para no intentar
        # ir a donde ya estoy.
        if len(self.ruta) > 0:
            self.ruta.pop(0) 
        
    def update(self, diccionario_nodos, lista_semaforos, lista_obstaculos): # <--- Argumento nuevo
        # 1. ¿Tengo ruta?
        if not self.ruta:
            return 

        nombre_objetivo = self.ruta[0]
        pos_objetivo = diccionario_nodos[nombre_objetivo]
        
        # Vectores y distancia al objetivo
        dir_x = pos_objetivo[0] - self.pos[0]
        dir_y = pos_objetivo[1] - self.pos[1]
        distancia_objetivo = math.hypot(dir_x, dir_y)

        # --- ÁRBOL DE DECISIÓN ---
        debo_frenar = False

        # REGLA 1: SEMÁFOROS (La que ya tenías)
        distancia_frenado_semaforo = 35 
        if distancia_objetivo < distancia_frenado_semaforo:
            semaforo_en_camino = None
            for s in lista_semaforos:
                if s.nodo_id == nombre_objetivo:
                    semaforo_en_camino = s
                    break
            if semaforo_en_camino and semaforo_en_camino.estado == "ROJO":
                debo_frenar = True

        # REGLA 2: OBSTÁCULOS CON CAMPO DE VISIÓN (FOV)
        radio_seguridad = 50 
        angulo_vision = 45 # Grados hacia cada lado (Cono de 90 grados total)

        for obs in lista_obstaculos:
            dx = obs.pos[0] - self.pos[0]
            dy = obs.pos[1] - self.pos[1]
            dist_obs = math.hypot(dx, dy)
            
            if dist_obs < radio_seguridad:
                # 1. Ya sabemos que está cerca.
                # 2. Ahora, ¿está enfrente?
                
                # Ángulo hacia el obstáculo
                angulo_obs = math.atan2(dy, dx)
                
                # Ángulo hacia donde se mueve el auto (Vector velocidad)
                # Si el auto está quieto, usamos el último movimiento o el objetivo
                # Para simplificar, calculamos el ángulo hacia el objetivo actual del grafo
                dir_obj_x = pos_objetivo[0] - self.pos[0]
                dir_obj_y = pos_objetivo[1] - self.pos[1]
                angulo_auto = math.atan2(dir_obj_y, dir_obj_x)
                
                # Diferencia de ángulos
                diff = math.degrees(angulo_obs - angulo_auto)
                
                # Normalizar el ángulo entre -180 y 180
                diff = (diff + 180) % 360 - 180
                
                # Si la diferencia es pequeña (está dentro del cono), FRENAR
                if abs(diff) < angulo_vision:
                    debo_frenar = True
                    print(f"¡Obstáculo a la vista! Dist: {int(dist_obs)} Ángulo: {int(diff)}")
                    break

        # --- ACTUADORES (Motores) ---
        if debo_frenar:
            pass # Frenar (Velocidad 0)
        else:
            # Moverse hacia el objetivo
            if distancia_objetivo <= self.velocidad:
                self.pos = list(pos_objetivo)
                self.ruta.pop(0) 
            else:
                dir_x = dir_x / distancia_objetivo
                dir_y = dir_y / distancia_objetivo
                self.pos[0] += dir_x * self.velocidad
                self.pos[1] += dir_y * self.velocidad

    def dibujar(self, pantalla):
        # Dibujamos el auto
        pygame.draw.circle(pantalla, ROJO, (int(self.pos[0]), int(self.pos[1])), 15)
        
        # (Opcional) Dibujar una linea pequeña indicando hacia dónde quiere ir
        if self.ruta:
            pass # Aquí podríamos dibujar una flechita