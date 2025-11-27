import pygame
import math
from configuracion import *
import random

class Auto:
    # Definicion del constructor del automovil, recibe la posicion en la que se genera
    # El sprite del vehiculo que tendra y la velocidad en la avanzara
    def __init__(self, pos_inicial, imagen_sprite, velocidad):
        # Posicion del vehiculo
        self.pos = list(pos_inicial) if pos_inicial is not None else None
        # De donde viene el vehiculo (De ningun lado cuando recien se genera)
        self.pos_anterior_nodo = list(pos_inicial) if pos_inicial is not None else [0,0]
        # La ruta que tomara el vehiculo
        self.ruta = []
        # Velocidad actual del vehiculo
        self.velocidad = velocidad
        # Velocidad maxima a la que puede ir
        self.velocidadmax = velocidad
        # Cuanto esperara hasta calcular nueva ruta
        self.cooldown_espera = 0
        
        # --- DEBUG Y ESTADO ---
        self.velocidad_actual = 0 
        self.font_debug = pygame.font.SysFont("Consolas", 10, bold=True)

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
        # Cuanto tiempo lleva parado el vehiculo para
        # Si lleva demasiado tiempo retroceder en pro de dejar pasar
        # a otro vehiculo si es que ese es el problema
        self.tiempo_parado = 0
        # Darle una aleatorieadad para que dos vehiculos no repliquen el mismo comportamiento
        self.max_tiempo_parado = random.randint(150, 250)
        
        # --- VARIABLES MODO REVERSA (BACKTRACKING) ---
        # Para evaluar cuando esta en reversa
        self.en_reversa = False
        # Pila de historial de los pasos y la direccion que tomo
        self.historial = [] 
        # Cuanto es lo maximo que puede retroceder
        self.max_historial = 50

    # Funcion para planificar la ruta del auto inteligente
    def planificar_ruta(self, ruta_nombres, diccionario_nodos=None):
        # La ruta que llevara
        self.ruta = ruta_nombres
        if len(self.ruta) > 0:
            # Quitamos el nodo actual (origen)
            self.ruta.pop(0)

            # Si hay un siguiente nodo y tenemos el mapa, giramos ya
            if len(self.ruta) > 0 and diccionario_nodos is not None:
                nombre_siguiente = self.ruta[0]
                if nombre_siguiente in diccionario_nodos:
                    destino_pos = diccionario_nodos[nombre_siguiente]
                    
                    # Calcular vector hacia el destino
                    dx = destino_pos[0] - self.pos[0]
                    dy = destino_pos[1] - self.pos[1]
                    
                    # Calcular el ángulo exacto hacia el nodo
                    self.angulo = math.atan2(dy, dx)

    def update(self, diccionario_nodos, lista_semaforos, lista_obstaculos, lista_npc):

        # Si es NPC esperar un poco anes de calcular la nueva ruta
        if self.cooldown_espera > 0 and self in lista_npc:
            self.cooldown_espera -= 1
            self.ruta = [] 
            self.velocidad_actual = 0
            return 

        # -----------------------------------------------------------
        # 1. LÓGICA DE REVERSA 
        # -----------------------------------------------------------
        if self.en_reversa:
            # Velocidad negativa, esto solo sirve para en el debug garantizar que esta en reversa
            self.velocidad_actual = -1 
            
            # Si hay hacia donde retroceder hacerlo
            if self.historial:
                # Obtenemos la ultima posicion
                prev_x, prev_y, prev_ang = self.historial[-1]
                # Esperamos que el camino hacia atras este libre
                camino_libre_atras = True
                
                # Definimos qué tan lejos chequeamos hacia atrás (ej. 40 pixeles)
                distancia_chequeo_trasero = 40 
                
                for obs in lista_obstaculos:
                    # Ignorarse a sí mismo
                    if hasattr(obs, 'pos') and obs.pos == self.pos:
                        continue
                    
                    # Calcular vector desde el Auto hacia el Obstáculo
                    dx = obs.pos[0] - self.pos[0]
                    dy = obs.pos[1] - self.pos[1]
                    dist = math.hypot(dx, dy)
                    
                    # Si el obstáculo está lo suficientemente cerca para preocuparnos
                    if dist < distancia_chequeo_trasero:
                        # Calculamos el ángulo hacia el obstáculo
                        angulo_obs = math.atan2(dy, dx)
                        
                        # Calculamos la diferencia con el ángulo actual del auto
                        diff = math.degrees(angulo_obs - self.angulo)
                        diff = (diff + 180) % 360 - 180
                        
                        # Si la diferencia es mayor a 135 o menor a -135, significa
                        # que el objeto está en el cono trasero (detrás del auto).
                        # (0 grados es frente, 180 o -180 es atrás)
                        # 120 grados da un cono amplio atrás
                        if abs(diff) > 120:  
                            # Si hay algo detras entonces no podemos movernos
                            camino_libre_atras = False
 
                            break
                # Solo moverse si el camino esta libre
                if camino_libre_atras:
                    # Si está libre atrás, procedemos a movernos al punto histórico
                    self.historial.pop()
                    self.pos = [prev_x, prev_y]
                    self.angulo = prev_ang 
                else:
                    # Si hay algo detrás, cancelamos reversa para intentar girar
                    self.en_reversa = False
                    self.tiempo_parado = 0 
            # Si no hay nada en el historial entonces solo queda esperar a que el entorno cambie
            else:
                self.en_reversa = False
                self.tiempo_parado = 0
                self.angulo += random.uniform(-0.8, 0.8) 
            return

        # -----------------------------------------------------------
        # LÓGICA NORMAL DE NAVEGACIÓN
        # -----------------------------------------------------------
        # Si no hay ruta entonces no avanzar hasta que se tenga una
        if not self.ruta:
            self.velocidad_actual = 0
            return
        # Obtener el siguiente nodo al que se va
        nombre_objetivo = self.ruta[0]
        # si ya no esta el siguiente nodo al que se dirige entonces solo queda cancelar la ruta
        if nombre_objetivo not in diccionario_nodos:
            self.ruta = []
            return
        # Obtener la posicion a la que se dirige
        pos_nodo_destino = diccionario_nodos[nombre_objetivo]

        # Como no hay curvas, ahora se obtienen lineas rectas del nodo en el que se esta al que se dirige
        rx_calle = pos_nodo_destino[0] - self.pos_anterior_nodo[0]
        ry_calle = pos_nodo_destino[1] - self.pos_anterior_nodo[1]
        # Linea recta concreta, se usa hypotenusa porque como pueden existir diagonales entonces ese es
        # el vector que se genera para llegar al siguiente nodo, en caso de que no haya rx la resultante sera ry 
        # y caso contrario sera rx
        # Al calcularse nodo a nodo, no se traza una resultante directa hacia el  nodo destino
        # sino los pequeños caminos que se pueden recorrer nodo a nodo
        dist_total_calle = math.hypot(rx_calle, ry_calle)

        # Obtener el vector unitario de cada direccion
        nx, ny = 0, 0
        if dist_total_calle > 0:
            nx = rx_calle / dist_total_calle
            ny = ry_calle / dist_total_calle

        # Para simular el carril izquierdo y el carril derecho simplemente
        # usamos la direccion y el ancho del carril
        # para dezplazar siempre a la derecha el auto, asi si va de arriba a abajo se mueve a la derecha y si va de abajo hacia
        # arriba a la derecha de esta direccion, simulando los carriles
        # Este mismo efecto ocurre las direcciones horizontales
        perp_x = -ny * self.ancho_carril
        perp_y =  nx * self.ancho_carril

        # obtenemos cuanto ha avanzado ahora el auto
        dx_auto = self.pos[0] - self.pos_anterior_nodo[0]
        dy_auto = self.pos[1] - self.pos_anterior_nodo[1]
        progreso_actual = dx_auto * nx + dy_auto * ny

        # El auto ve 60 pixeles al frente
        LOOKAHEAD = 60 
        # Se va ajustando lo que ve el auto segun lo que lo que avanza
        target_dist = progreso_actual + LOOKAHEAD
        # Si ve que se va a salir de la calle
        if target_dist > dist_total_calle:
            # Entonces ajustamos para que el auto no se salga de la calle
            target_dist = dist_total_calle
        # Ya estando establecido en el limite podemos crear las coordenadas exactas a 
        # recorrer desde el nodo actual al que sigue
        target_x = self.pos_anterior_nodo[0] + (nx * target_dist) + perp_x
        target_y = self.pos_anterior_nodo[1] + (ny * target_dist) + perp_y

        # Calcular desde donde se encuentra el auto  a las coordenadas precisas
        dir_x = target_x - self.pos[0]
        dir_y = target_y - self.pos[1]
        # Trazamos una resultante a este objetivo
        distancia_objetivo = math.hypot(dir_x, dir_y)
        # si no hemos llegado ahi entonces trazamos el vector unitario
        if distancia_objetivo != 0:
            ndx = dir_x / distancia_objetivo
            ndy = dir_y / distancia_objetivo
        else:
        # si ya llegamos entonces no hay una direccion a la que ir
            ndx, ndy = 0, 0
        
        # Calcular ángulo deseado al que debe girar el coche para alcanzar ese punto resultante
        self.angulo = math.atan2(dir_y, dir_x)

        # ------------------------------
        #  EVASIÓN DE OBSTÁCULOS (FRONTAL)
        # ------------------------------

        # Para reducir la velocidad gradualmente
        factor_velocidad = 1.0

        # Vemos todos los obstaculos
        for obs in lista_obstaculos:
            # Ignorarse a sí mismo
            if obs is self:
                continue
            # Calculamos la distancia del obstaculo al vehiculo
            dx = obs.pos[0] - self.pos[0]
            dy = obs.pos[1] - self.pos[1]
            dist = math.hypot(dx, dy)
            
            # En que parte del auto esta el obstaculo
            angulo_obs = math.atan2(dy, dx)
            diff = math.degrees(angulo_obs - self.angulo)
            diff = (diff + 180) % 360 - 180
            
            # Verificar que hay una distancia en la que no puedo chocar del auto
            dist_lateral = dx * (-ndy) + dy * (ndx)
            # Pero que sea lo suficientemente grande a la distancia del auto
            ancho_seguro = self.radio + 5

            # Ahora se debe cumplir que, si el obstaculo esta en la distancia de vision
            if dist < DISTANCIA_VISION: 
                # Esta en el angulo de vision frontal
                if abs(diff) < 45:    
                    # Y no hay distancia segura por la que pasar
                    if abs(dist_lateral) < ancho_seguro:
                        # Cuando se llegue a la distancia de seguridad
                        if dist < DISTANCIA_STOP:
                            # Frenar el auto
                            factor_velocidad = 0.0
                        # Si se esta cerca de la distancia de seguridad reducir la velocidad segun que tan
                        # cerca se esta
                        elif dist < (DISTANCIA_STOP + 30):
                            factor_velocidad = 0.3
                        else:
                            factor_velocidad = 0.6
                        break
        # Pasado el obstaculo volver a la velocidad original
        velocidad_base = self.velocidadmax
        # Guardamos la velocidad real para dibujarla luego
        self.velocidad_actual = velocidad_base * factor_velocidad

        # ------------------------------
        #  DETECTOR DE ATASCOS
        # ------------------------------
        # SI estoy parado, contar cuanto llevo parado
        if self.velocidad_actual < 0.1:
            self.tiempo_parado += 1
        else:
            self.tiempo_parado = 0 
        # Si llevo mucho tiempo parado entonces ir de reversa
        if self.tiempo_parado > self.max_tiempo_parado:
            self.en_reversa = True
            return 

        # ------------------------------
        #    SEMÁFOROS
        # ------------------------------
        # Asumimos que no hay semaforo
        debo_frenar = False
        # Vemos en todos los semaforos
        for s in lista_semaforos:
            # Cual esta cerca de nuestro rango de vision
            dx_s = s.pos[0] - self.pos[0]
            dy_s = s.pos[1] - self.pos[1]
            dist_s = math.hypot(dx_s, dy_s)

            # Si esta en nuestro rango de vision
            # Tanto de distancia
            if dist_s < DISTANCIA_VISION:
                # Como de angulo
                angulo_sem = math.atan2(dy_s, dx_s)
                diff_sem = math.degrees(angulo_sem - self.angulo)
                diff_sem = (diff_sem + 180) % 360 - 180
                
                # Si el auto lo "ve"
                if abs(diff_sem) < 40:
                    # Y esta en rojo
                    if s.estado == "ROJO":
                        # Deneterse a cierta distancia
                        if dist_s < DISTANCIA_STOP + 40:
                            debo_frenar = True
                            break
        # si el auto no debe frenar entonces
        if not debo_frenar:
            # Ya llegue?
            rabbit_llegado = (target_dist >= dist_total_calle)
            
            # Si ya llegue y estoy a una distancia considerable entonces
            if rabbit_llegado and distancia_objetivo <= self.velocidad_actual + 2:
                # El nuevo nodo se vuelve el nodo anterior
                self.pos_anterior_nodo = list(pos_nodo_destino)
                # Alineamos el carro para que este pereparado para su siguiente destino
                final_x = pos_nodo_destino[0] + perp_x
                final_y = pos_nodo_destino[1] + perp_y
                self.pos = [final_x, final_y]
                # pasamos al siguiente nodo
                self.ruta.pop(0)
                # Limpiamos el historial para evitar errores, pues el calculo se hace de nodo a nodo
                self.historial.clear() 
                # nueva posicion a retroceder
                self.historial.append((self.pos[0], self.pos[1], self.angulo))
                # Esperamosa antes de recorrer nueva ruta
                if not self.ruta:
                    self.cooldown_espera = COOLD_DOWN_RUTA
            else:
                # Si no he llegado entonces seguir moviendome por la arista
                self.pos[0] += ndx * self.velocidad_actual
                self.pos[1] += ndy * self.velocidad_actual

                # Si no estoy en modo reversa puedo grabar el historial de posiciones
                if self.velocidad_actual > 0.1 and not self.en_reversa:
                    grabar = True
                    # Si ya tenemos algo grabado, comprobamos para no volver a guardar lo mismo varias veces
                    if self.historial:
                        ult_x, ult_y, _ = self.historial[-1]
                        dist_reciente = math.hypot(self.pos[0]-ult_x, self.pos[1]-ult_y)
                        # Grabar cada 3 pixeles
                        if dist_reciente < 3: 
                            grabar = False
                    # Si no he grabado nada o estoy a una distancia suficientemente alta
                    # grabar esa nueva posicion
                    if grabar:
                        self.historial.append((self.pos[0], self.pos[1], self.angulo))
                        if len(self.historial) > self.max_historial:
                            self.historial.pop(0)

    def asignar_ruta_aleatoria(self, mapa):
        # Tiempo de espera para nueva ruta
        if self.cooldown_espera > 0:
            return
        # Obtenemos los nodos disponibles
        claves = list(mapa.nodos.keys())
        # Si no hay dos, entonces no hay otro punto al que viajar
        if len(claves) < 2: return

        # Declaramos origen
        origen = None
        # Si tengo una ruta
        if self.ruta:
            # Tomamos el nodo en el que me encuentro
            origen = self.ruta[0]
        # Si no
        else:
            # Definimos otro origen
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
        # Quitamos el nodo de origen de todo el mapa al que podemos viajar
        posibles = [k for k in claves if k != origen]
        if not posibles: return
        # Tomamos un destino al azar
        destino = random.choice(posibles)
        # Calculamos la mejor ruta
        camino = mapa.dijkstra(origen, destino)
        # Si existe un camino al que ir
        if camino and len(camino) > 1:
            # Planificamos la ruta ya en coordenadas fisicas
            self.planificar_ruta(camino, mapa.nodos)
        else:
            # No hay camino, no hay ruta
            self.ruta = []

    # Dibujar el auto
    def dibujar(self, pantalla):
        if self.pos is None: return

        # 1. Sprite del auto
        rotacion_pygame = -math.degrees(self.angulo) + 90
        
        self.image = pygame.transform.rotate(self.imagen_original, rotacion_pygame)
        self.image.set_alpha(255) 

        self.rect = self.image.get_rect(center=(int(self.pos[0]), int(self.pos[1])))
        pantalla.blit(self.image, self.rect)

        # 2. DEBUG INFO
        # Texto: Velocidad, Posición, Estado
        txt_vel = f"V: {self.velocidad_actual:.1f}"
        txt_pos = f"P: {int(self.pos[0])},{int(self.pos[1])}"
        txt_est = "REV" if self.en_reversa else ("WAIT" if self.cooldown_espera > 0 else "RUN")

        # Crear superficies de texto (Blanco con fondo negro)
        surf_vel = self.font_debug.render(txt_vel, True, (255, 255, 255), (0, 0, 0))
        surf_pos = self.font_debug.render(txt_pos, True, (255, 255, 255), (0, 0, 0))
        surf_est = self.font_debug.render(txt_est, True, ROJO if self.en_reversa else (AMARILLO if txt_est == "WAIT" else (0, 255, 0)), (0,0,0))

        # Posicionamiento encima del auto
        base_y = self.rect.top - 35
        center_x = self.pos[0]

        rect_vel = surf_vel.get_rect(center=(center_x, base_y))
        rect_pos = surf_pos.get_rect(center=(center_x, base_y + 10))
        rect_est = surf_est.get_rect(center=(center_x, base_y + 20))

        pantalla.blit(surf_vel, rect_vel)
        pantalla.blit(surf_pos, rect_pos)
        pantalla.blit(surf_est, rect_est)
