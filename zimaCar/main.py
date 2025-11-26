import pygame
import sys
import math
import random
import threading
import time
from configuracion import *
from clases.grafo import Grafo
from clases.auto import Auto
from clases.semaforo import Semaforo
from clases.obstaculo import Obstaculo

pygame.init()
pantalla = pygame.display.set_mode((ANCHO, ALTO))
pygame.display.set_caption("Simulación Completa - Editor & Tráfico (Pixel Art)")
reloj = pygame.time.Clock()

# --- CARGA DE ASSETS Y FUNCIONES AUXILIARES ---
try:
    # 1. Cargar la imagen original
    imagen_original = pygame.image.load("carro.png").convert_alpha()
    imagen_delorean =  pygame.image.load("delorean.png").convert_alpha()
    # 2. Redimensionar
    NUEVO_ANCHO = 36
    NUEVO_ALTO = 70
    sprite_auto_base = pygame.transform.scale(imagen_original, (NUEVO_ANCHO, NUEVO_ALTO))
    sprite_auto_base_main = pygame.transform.scale(imagen_delorean, (NUEVO_ANCHO, NUEVO_ALTO))
except FileNotFoundError:
    print("ERROR FATAL: No se encontró 'carro.png'. Asegúrate de que el archivo esté en el directorio.")
    sys.exit()

def teñir_imagen(imagen_base, color):
    """
    Crea una copia de la imagen base y la tiñe usando el modo de mezcla MULTIPLY.
    """
    imagen_teñida = imagen_base.copy()
    superficie_color = pygame.Surface(imagen_teñida.get_size()).convert_alpha()
    superficie_color.fill(color)
    imagen_teñida.blit(superficie_color, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return imagen_teñida

def crear_npc(lista_npcs):
    nodo_inicio = random.choice(list(mapa.nodos.keys()))
    color_rand = random.choice(colores_posibles)
    
    # Crear la textura teñida para este NPC
    sprite_npc = teñir_imagen(sprite_auto_base, color_rand)
    velocidad = random.choice(VELOCIDADES_NPC)
    npc = Auto(mapa.nodos[nodo_inicio], sprite_npc,velocidad)

    lista_npcs.append(npc)


# Crear el auto del jugador
mi_auto = Auto(None, sprite_auto_base_main,VELOCIDAD_AUTO)
mi_auto.historial = [] 

# --- INSTANCIAS ---
mapa = Grafo()

# Función auxiliar para conectar con distancia real en el setup inicial
def conectar_realista(n1, n2):
    if n1 in mapa.nodos and n2 in mapa.nodos:
        p1 = mapa.nodos[n1]
        p2 = mapa.nodos[n2]
        dist = int(math.hypot(p1[0]-p2[0], p1[1]-p2[1]))
        mapa.conectar(n1, n2, dist)

# --- CREACIÓN INICIAL DEL MAPA ---
mapa.agregar_nodo("N1", (200, 100))   # Arriba-Izq
mapa.agregar_nodo("N2", (640, 100))   # Arriba-Centro
mapa.agregar_nodo("N3", (1080, 100))  # Arriba-Der

mapa.agregar_nodo("N4", (200, 360))   # Medio-Izq
mapa.agregar_nodo("N5", (640, 360))   # CENTRO
mapa.agregar_nodo("N6", (1080, 360))  # Medio-Der

mapa.agregar_nodo("N7", (200, 620))   # Abajo-Izq
mapa.agregar_nodo("N8", (640, 620))   # Abajo-Centro
mapa.agregar_nodo("N9", (1080, 620))  # Abajo-Der

# Conexiones Horizontales
conectar_realista("N1", "N2")
conectar_realista("N2", "N3")
conectar_realista("N4", "N5")
conectar_realista("N5", "N6")
conectar_realista("N7", "N8")
conectar_realista("N8", "N9")

# Conexiones Verticales
conectar_realista("N1", "N4")
conectar_realista("N4", "N7")
conectar_realista("N2", "N5")
conectar_realista("N5", "N8")
conectar_realista("N3", "N6")
conectar_realista("N6", "N9")

# Diagonales
conectar_realista("N4", "N8")
conectar_realista("N2", "N6")

# --- ENTIDADES (Autos con Sprites) ---

colores_posibles = [
    ROJO, VERDE, AZUL, AMARILLO, NARANJA, 
    (200, 50, 200), # Violeta
    (50, 200, 200), # Cian
    (150, 150, 150) # Gris oscuro
]


semaforos = [
    Semaforo("N5", mapa.nodos["N5"], "ROJO", 150),   
    Semaforo("N2", mapa.nodos["N2"], "VERDE", 150),  
    Semaforo("N8", mapa.nodos["N8"], "ROJO", 150),   
    Semaforo("N4", mapa.nodos["N4"], "VERDE", 100),  
    Semaforo("N6", mapa.nodos["N6"], "ROJO", 100)    
]

lista_npcs = []
# Crear 5 NPCs con colores aleatorios
for _ in range(5):
    crear_npc(lista_npcs)

lista_obstaculos = []

# Sincronización
state_lock = threading.Lock()
running_flag = {"running": True}

# Variables de Control (UI/editor)
modo_editor = False
contador_nodos = 1
nodo_seleccionado_para_conectar = None

seleccion_origen = None
seleccion_destino = None
nodo_bajo_mouse = None 

# -------------------------------
#   HILO: lógica del auto
# -------------------------------
def hilo_auto():
    target_hz = 60.0
    delay = 1.0 / target_hz
    while running_flag["running"]:
        with state_lock:
            nodos_copy = dict(mapa.nodos)
            sems_copy = list(semaforos)
            obst_base = list(lista_obstaculos)
            npcs_copy = list(lista_npcs)

        obst_for_auto = obst_base + npcs_copy

        try:
            mi_auto.update(nodos_copy, sems_copy, obst_for_auto, lista_npcs)
        except Exception as e:
            print("[hilo_auto] excepción:", e)

        time.sleep(delay)

# -------------------------------
#   HILO: lógica de NPCs
# -------------------------------
def hilo_npcs():
    target_hz = 60.0
    delay = 1.0 / target_hz
    while running_flag["running"]:
        with state_lock:
            nodos_copy = dict(mapa.nodos)
            sems_copy = list(semaforos)
            obst_base = list(lista_obstaculos)
            npcs_snapshot = list(lista_npcs)
            mi_auto_snapshot = mi_auto if mi_auto.pos is not None else None

        for npc in npcs_snapshot:
            try:
                others = [o for o in npcs_snapshot if o is not npc]
                obst_for_npc = obst_base + others
                if mi_auto_snapshot is not None:
                    obst_for_npc = obst_for_npc + [mi_auto_snapshot]

                npc.update(nodos_copy, sems_copy, obst_for_npc, lista_npcs)
                
                if not npc.ruta:
                    with state_lock:
                        # Nota: Aquí no pasamos es_jugador=True, por lo que los NPCs
                        # no alterarán el dibujo de tu ruta roja.
                        npc.asignar_ruta_aleatoria(mapa)
                    
            except Exception as e:
                print("[hilo_npcs] excepción:", e)

        time.sleep(delay)

# -------------------------------
#   Lanzar hilos
# -------------------------------
thread_auto = threading.Thread(target=hilo_auto, daemon=True)
thread_npcs = threading.Thread(target=hilo_npcs, daemon=True)
thread_auto.start()
thread_npcs.start()

# -------------------------------
#       BUCLE PRINCIPAL
# -------------------------------
try:
    while True:
        # 1. ACTUALIZAR MOUSE PRIMERO
        mouse_pos = pygame.mouse.get_pos()
        nodo_bajo_mouse = None
        
        with state_lock:
            lista_items_nodos = list(mapa.nodos.items())
        
        for nombre, pos in lista_items_nodos:
            if math.hypot(mouse_pos[0]-pos[0], mouse_pos[1]-pos[1]) < RADIO_NODO:
                nodo_bajo_mouse = nombre
                break

        # 2. PROCESAR EVENTOS
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                running_flag["running"] = False
                pygame.quit()
                sys.exit()

            if evento.type == pygame.KEYDOWN:
                # --- CAMBIO DE MODO ---
                if evento.key == pygame.K_s:
                    with state_lock:
                        modo_editor = False
                        nodo_seleccionado_para_conectar = None
                    print("--- SIMULACIÓN ACTIVADA ---")

                elif evento.key == pygame.K_e:
                    with state_lock:
                        modo_editor = True
                        nodo_seleccionado_para_conectar = None
                    print("--- EDITOR ACTIVADO ---")


                # --- AGREGAR/QUITAR SEMÁFORO CON 'F' (TOGGLE) ---
                elif evento.key == pygame.K_f:
                    if nodo_bajo_mouse:
                        sem_encontrado = None
                        with state_lock:
                            for s in semaforos:
                                if s.nodo_id == nodo_bajo_mouse:
                                    sem_encontrado = s
                                    break
                            
                            if sem_encontrado:
                                semaforos.remove(sem_encontrado)
                                print(f"Semáforo ELIMINADO en {nodo_bajo_mouse}")
                            else:
                                semaforos.append(Semaforo(nodo_bajo_mouse, mapa.nodos[nodo_bajo_mouse]))
                                print(f"Semáforo CREADO en {nodo_bajo_mouse}")
                
                # --- AGREGAR/QUITAR NPC ---
                elif evento.key == pygame.K_n:
                    crear_npc(lista_npcs)
                
                elif evento.key == pygame.K_q:
                    if lista_npcs:
                        lista_npcs.pop()

            # ================= LÓGICA EDITOR =================
            if modo_editor:
                if evento.type == pygame.MOUSEBUTTONDOWN:
                    if evento.button == 1:  # Clic Izq
                        if nodo_bajo_mouse:
                            # Conectar Nodos
                            if nodo_seleccionado_para_conectar is None:
                                nodo_seleccionado_para_conectar = nodo_bajo_mouse
                            else:
                                if nodo_seleccionado_para_conectar != nodo_bajo_mouse:
                                    with state_lock:
                                        conectar_realista(nodo_seleccionado_para_conectar, nodo_bajo_mouse)
                                    nodo_seleccionado_para_conectar = None
                                else:
                                    nodo_seleccionado_para_conectar = None
                        else:
                            # Crear Nodo
                            nombre = f"E{contador_nodos}"
                            with state_lock:
                                mapa.agregar_nodo(nombre, mouse_pos)
                                contador_nodos += 1

                    elif evento.button == 3:  # Clic Der (Borrar)
                        if nodo_bajo_mouse:
                            with state_lock:
                                mapa.eliminar_nodo(nodo_bajo_mouse)
                                semaforos = [s for s in semaforos if s.nodo_id != nodo_bajo_mouse]

            # ================= LÓGICA SIMULACIÓN =================
            else:
                if evento.type == pygame.MOUSEBUTTONDOWN:
                    if evento.button == 1:  # Clic Izq (Navegar)
                        if nodo_bajo_mouse:
                            with state_lock:
                                if len(mi_auto.ruta) > 0:
                                    obj_actual = mi_auto.ruta[0]
                                    # MODIFICADO: Agregado es_jugador=True
                                    camino = mapa.dijkstra(obj_actual, nodo_bajo_mouse, es_jugador=True)
                                    if camino:
                                        mi_auto.ruta = camino
                                        seleccion_origen = nodo_bajo_mouse
                                        
                                else:
                                    if seleccion_origen is None:
                                        seleccion_origen = nodo_bajo_mouse
                                        # Visualizar nodo seleccionado
                                        mapa.camino_resaltado = [seleccion_origen]
                                    else:
                                        seleccion_destino = nodo_bajo_mouse
                                        # MODIFICADO: Agregado es_jugador=True
                                        camino = mapa.dijkstra(seleccion_origen, seleccion_destino, es_jugador=True)
                                        if camino:
                                            mi_auto.planificar_ruta(camino)
                                            pos_origen = list(mapa.nodos[seleccion_origen])
                                            mi_auto.pos = list(pos_origen)
                                            mi_auto.pos_anterior_nodo = list(pos_origen)
                                        seleccion_origen = seleccion_destino
                                        seleccion_destino = None

                    elif evento.button == 3:  # Clic Der (Obstáculos)
                        borrado = False
                        with state_lock:
                            for obs in list(lista_obstaculos):
                                if math.hypot(mouse_pos[0]-obs.pos[0], mouse_pos[1]-obs.pos[1]) < obs.radio + 5:
                                    lista_obstaculos.remove(obs)
                                    borrado = True
                                    break
                            if not borrado:
                                lista_obstaculos.append(Obstaculo(mouse_pos))

        # --- ACTUALIZACIÓN (Main Thread) ---
        for s in semaforos:
            s.update()

        # --- DIBUJADO ---
        imagen_fondo_base = pygame.Surface((ANCHO, ALTO))
        try:
            textura = pygame.image.load("fondo.png").convert()
            ancho_t, alto_t = textura.get_size()
            for x in range(0, ANCHO, ancho_t):
                for y in range(0, ALTO, alto_t):
                    imagen_fondo_base.blit(textura, (x, y))
        except FileNotFoundError:
            imagen_fondo_base.fill(NEGRO)

        fondo_surface = imagen_fondo_base.copy()
        mapa.dibujar(fondo_surface)
        pantalla.blit(fondo_surface, (0, 0))

        if modo_editor and nodo_seleccionado_para_conectar:
            if nodo_seleccionado_para_conectar in mapa.nodos:
                origen = mapa.nodos[nodo_seleccionado_para_conectar]
                pygame.draw.line(pantalla, AMARILLO, origen, pygame.mouse.get_pos(), 2)

        with state_lock:
            npc_snapshot = list(lista_npcs)
            auto_pos = mi_auto.pos
            sem_snapshot = list(semaforos)
            obs_snapshot = list(lista_obstaculos)

        # Dibujar entidades
        for obs in obs_snapshot:
            obs.dibujar(pantalla)
        for s in sem_snapshot:
            s.dibujar(pantalla)
            
        for npc in npc_snapshot:
            npc.dibujar(pantalla)
        if auto_pos is not None:
            mi_auto.dibujar(pantalla)

        # UI
        fuente = pygame.font.SysFont("Arial", 24)
        txt = "MODO: EDITOR (Usa 'S' para cambiar a la simulacion)" if modo_editor else "MODO: SIMULACIÓN (Usa 'E') Para cambiar al editor"
        col = AMARILLO if modo_editor else BLANCO
        pantalla.blit(fuente.render(txt, True, col), (10, 10))
        
        txt_f = "F: Agregar/Quitar Semáforos"
        pantalla.blit(fuente.render(txt_f, True, BLANCO), (10, 40))
        txt_q = "N: Agregar NPC, Q: Quitar un NPC al azar"
        pantalla.blit(fuente.render(txt_q, True, BLANCO), (500, 10))
        pygame.display.flip()
        reloj.tick(60)

except SystemExit:
    running_flag["running"] = False
except Exception as e:
    print("Excepción en main loop:", e)
    running_flag["running"] = False
    pygame.quit()
    raise