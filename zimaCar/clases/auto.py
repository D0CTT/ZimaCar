import pygame
import math
from configuracion import *
import random
import threading
import time

class Auto:
    def __init__(self, pos_inicial, imagen_sprite, velocidad):
        self.pos = list(pos_inicial) if pos_inicial is not None else None
        self.pos_anterior_nodo = list(pos_inicial) if pos_inicial is not None else [0,0]
        self.ruta = []
        self.velocidad = velocidad
        self.velocidadmax = velocidad
        self.cooldown_espera = 0
        # --- GESTIÓN DE SPRITE ---
        self.imagen_original = imagen_sprite
        self.image = self.imagen_original.copy()
        self.rect = self.image.get_rect()
        
        # Radio de colisión
        avg_dim = (self.rect.width + self.rect.height) / 2
        self.radio = avg_dim / 2 * 0.9 

        self.angulo = 0 
        self.ancho_carril = 22  

        # --- VARIABLES ANTI-BLOQUEO ---
        self.tiempo_parado = 0
        self.max_tiempo_parado = random.randint(150, 250)
        
        # --- VARIABLES MODO REVERSA (BACKTRACKING) ---
        self.en_reversa = False
        self.historial = [] 
        self.max_historial = 50

    def planificar_ruta(self, ruta_nombres):
        self.ruta = ruta_nombres
        if len(self.ruta) > 0:
            self.ruta.pop(0)

    def update(self, diccionario_nodos, lista_semaforos, lista_obstaculos, lista_npc):
        if self.cooldown_espera > 0 and self in lista_npc:
            self.cooldown_espera -= 1
            # Mientras espera, borramos ruta (está parado), pero ahora será SÓLIDO
            self.ruta = [] 
            return # Salimos de la función, el auto no se mueve en este frame

        # -----------------------------------------------------------
        # 1. LÓGICA DE REVERSA MEJORADA
        # -----------------------------------------------------------
        if self.en_reversa:
            if self.historial:
                prev_x, prev_y, prev_ang = self.historial[-1]
                
                camino_libre_atras = True
                radio_seguridad = self.radio * 2 + 5 
                
                for obs in lista_obstaculos:
                    # Ignorarse a sí mismo
                    if hasattr(obs, 'pos') and obs.pos == self.pos:
                        continue
                    
                    # (ELIMINADO: Ya no ignoramos autos sin ruta)

                    dx = prev_x - obs.pos[0]
                    dy = prev_y - obs.pos[1]
                    dist = math.hypot(dx, dy)
                    
                    if dist < radio_seguridad:
                        camino_libre_atras = False
                        break
                
                if camino_libre_atras:
                    self.historial.pop()
                    self.pos = [prev_x, prev_y]
                    self.angulo = prev_ang 
                else:
                    self.en_reversa = False
                    self.tiempo_parado = 0 
            else:
                self.en_reversa = False
                self.tiempo_parado = 0
                self.angulo += random.uniform(-0.8, 0.8) 
            return

        # -----------------------------------------------------------
        # LÓGICA NORMAL DE NAVEGACIÓN
        # -----------------------------------------------------------
        if not self.ruta:
            return

        nombre_objetivo = self.ruta[0]
        if nombre_objetivo not in diccionario_nodos:
            self.ruta = []
            return

        pos_nodo_destino = diccionario_nodos[nombre_objetivo]

        rx_calle = pos_nodo_destino[0] - self.pos_anterior_nodo[0]
        ry_calle = pos_nodo_destino[1] - self.pos_anterior_nodo[1]
        dist_total_calle = math.hypot(rx_calle, ry_calle)

        nx, ny = 0, 0
        if dist_total_calle > 0:
            nx = rx_calle / dist_total_calle
            ny = ry_calle / dist_total_calle

        perp_x = -ny * self.ancho_carril
        perp_y =  nx * self.ancho_carril

        dx_auto = self.pos[0] - self.pos_anterior_nodo[0]
        dy_auto = self.pos[1] - self.pos_anterior_nodo[1]
        progreso_actual = dx_auto * nx + dy_auto * ny

        LOOKAHEAD = 60 
        target_dist = progreso_actual + LOOKAHEAD
        if target_dist > dist_total_calle:
            target_dist = dist_total_calle

        target_x = self.pos_anterior_nodo[0] + (nx * target_dist) + perp_x
        target_y = self.pos_anterior_nodo[1] + (ny * target_dist) + perp_y

        dir_x = target_x - self.pos[0]
        dir_y = target_y - self.pos[1]
        distancia_objetivo = math.hypot(dir_x, dir_y)

        if distancia_objetivo != 0:
            ndx = dir_x / distancia_objetivo
            ndy = dir_y / distancia_objetivo
        else:
            ndx, ndy = 0, 0
        
        target_angle = math.atan2(dir_y, dir_x)
        self.angulo = target_angle

        # ------------------------------
        #  EVASIÓN DE OBSTÁCULOS
        # ------------------------------
        factor_velocidad = 1.0

        for obs in lista_obstaculos:
            # (ELIMINADO: Ya no ignoramos autos sin ruta)
            
            # Ignorarse a sí mismo
            if obs is self:
                continue

            dx = obs.pos[0] - self.pos[0]
            dy = obs.pos[1] - self.pos[1]
            dist = math.hypot(dx, dy)
            
            angulo_obs = math.atan2(dy, dx)
            diff = math.degrees(angulo_obs - self.angulo)
            diff = (diff + 180) % 360 - 180
            
            dist_lateral = dx * (-ndy) + dy * (ndx)
            ancho_seguro = self.radio + 5

            if dist < DISTANCIA_VISION: 
                if abs(diff) < 45:    
                    if abs(dist_lateral) < ancho_seguro:
                        if dist < DISTANCIA_STOP:
                            factor_velocidad = 0.0
                        elif dist < (DISTANCIA_STOP + 30):
                            factor_velocidad = 0.3
                        else:
                            factor_velocidad = 0.6
                        break

        velocidad_base = self.velocidadmax
        velocidad_actual = velocidad_base * factor_velocidad

        # ------------------------------
        #  DETECTOR DE ATASCOS
        # ------------------------------
        if velocidad_actual < 0.1:
            self.tiempo_parado += 1
        else:
            self.tiempo_parado = 0 

        if self.tiempo_parado > self.max_tiempo_parado:
            self.en_reversa = True
            return 

        # ------------------------------
        #    SEMÁFOROS
        # ------------------------------
        debo_frenar = False
        for s in lista_semaforos:
            dx_s = s.pos[0] - self.pos[0]
            dy_s = s.pos[1] - self.pos[1]
            dist_s = math.hypot(dx_s, dy_s)

            if dist_s < DISTANCIA_VISION:
                angulo_sem = math.atan2(dy_s, dx_s)
                diff_sem = math.degrees(angulo_sem - self.angulo)
                diff_sem = (diff_sem + 180) % 360 - 180
                
                if abs(diff_sem) < 40:
                    if s.estado == "ROJO":
                        if dist_s < DISTANCIA_STOP + 40:
                            debo_frenar = True
                            break

        if not debo_frenar:
            rabbit_llegado = (target_dist >= dist_total_calle)
            
            if rabbit_llegado and distancia_objetivo <= velocidad_actual + 2:
                self.pos_anterior_nodo = list(pos_nodo_destino)
                final_x = pos_nodo_destino[0] + perp_x
                final_y = pos_nodo_destino[1] + perp_y
                self.pos = [final_x, final_y]
                self.ruta.pop(0)
                
                self.historial.clear() 
                self.historial.append((self.pos[0], self.pos[1], self.angulo))
                
                if not self.ruta:
                    self.cooldown_espera = COOLD_DOWN_RUTA
            else:
                self.pos[0] += ndx * velocidad_actual
                self.pos[1] += ndy * velocidad_actual

                if velocidad_actual > 0.1 and not self.en_reversa:
                    grabar = True
                    if self.historial:
                        ult_x, ult_y, _ = self.historial[-1]
                        dist_reciente = math.hypot(self.pos[0]-ult_x, self.pos[1]-ult_y)
                        if dist_reciente < 3: 
                            grabar = False
                    
                    if grabar:
                        self.historial.append((self.pos[0], self.pos[1], self.angulo))
                        if len(self.historial) > self.max_historial:
                            self.historial.pop(0)

    def dibujar(self, pantalla):
        if self.pos is None: return

        rotacion_pygame = -math.degrees(self.angulo) + 90
        
        self.image = pygame.transform.rotate(self.imagen_original, rotacion_pygame)
        
        # (ELIMINADO: Efecto fantasma/transparencia)
        self.image.set_alpha(255) # Siempre opaco

        self.rect = self.image.get_rect(center=(int(self.pos[0]), int(self.pos[1])))
        pantalla.blit(self.image, self.rect)

    def asignar_ruta_aleatoria(self, mapa):
        if self.cooldown_espera > 0:
            return
        claves = list(mapa.nodos.keys())
        if len(claves) < 2: return

        origen = None
        if self.ruta:
            origen = self.ruta[0]
        else:
            dist_min = float('inf')
            for nombre, pos in mapa.nodos.items():
                d = math.hypot(self.pos[0]-pos[0], self.pos[1]-pos[1])
                if d < dist_min:
                    dist_min = d
                    origen = nombre
            
            if dist_min > 50: 
                origen = random.choice(claves)
                self.pos = list(mapa.nodos[origen])
                self.pos_anterior_nodo = list(mapa.nodos[origen])

        posibles = [k for k in claves if k != origen]
        if not posibles: return
        
        destino = random.choice(posibles)
        camino = mapa.dijkstra(origen, destino)

        if camino and len(camino) > 1:
            self.planificar_ruta(camino)
        else:
            self.ruta = []