import pygame
import sys
from configuracion import *
from clases.grafo import Grafo
from clases.auto import Auto
from clases.semaforo import Semaforo
from clases.obstaculo import Obstaculo
from clases.npc import AutoNPC

# Inicialización de Pygame
pygame.init()
pantalla = pygame.display.set_mode((ANCHO, ALTO))
pygame.display.set_caption("Simulación Auto Autónomo - Dijkstra + Árboles")
reloj = pygame.time.Clock()

# --- CREACIÓN DEL MUNDO (Instancias) ---
mapa = Grafo()

# Vamos a crear unos nodos de prueba para ver algo en pantalla
mapa.agregar_nodo("A", (100, 300))
mapa.agregar_nodo("B", (400, 100))
mapa.agregar_nodo("C", (400, 500))
mapa.conectar("A", "B")
mapa.conectar("A", "C")
mapa.conectar("B", "C")

# Crear el auto en el nodo A
mi_auto = Auto(mapa.nodos["A"])

seleccion_origen = None
seleccion_destino = None

# --- SEMÁFOROS ---
# Vamos a poner semáforos en el nodo B y el nodo C (ajusta según tus nodos)
semaforos = []
# Sintaxis: Semaforo(Nombre_Nodo, Coordenadas_Nodo, Estado_Inicial, Tiempo)
semaforos.append(Semaforo("B", mapa.nodos["B"], "ROJO", 200))
semaforos.append(Semaforo("C", mapa.nodos["C"], "VERDE", 300))

lista_npcs = []
# Un auto que va y viene entre B y C
taxi1 = AutoNPC(1, ["B", "C"], mapa.nodos)
lista_npcs.append(taxi1)

lista_obstaculos = []

# --- BUCLE PRINCIPAL ---
while True:
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        
        # --- NUEVO: DETECTAR CLIC IZQUIERDO ---
        # --- DENTRO DEL BUCLE FOR EVENTOS en main.py ---
        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            mouse_pos = pygame.mouse.get_pos()
            
            # 1. Detectar qué nodo se clicó
            nodo_clicado = None
            for nombre, pos in mapa.nodos.items():
                distancia = ((mouse_pos[0] - pos[0])**2 + (mouse_pos[1] - pos[1])**2)**0.5
                if distancia < RADIO_NODO:
                    nodo_clicado = nombre
                    break
                    
            
            if nodo_clicado:
                # CASO A: El auto YA se está moviendo (Redirección al vuelo)
                if len(mi_auto.ruta) > 0:
                    print(f"Redireccionando hacia: {nodo_clicado}")
                    
                    # El origen del nuevo camino es el nodo al que está yendo AHORA MISMO
                    objetivo_actual = mi_auto.ruta[0]
                    
                    # Calculamos ruta desde el objetivo actual hasta el nuevo clic
                    camino = mapa.dijkstra(objetivo_actual, nodo_clicado)
                    
                    # TRUCO: Sobreescribimos la ruta DIRECTAMENTE sin usar planificar_ruta()
                    # Así evitamos que el auto borre el primer nodo (porque aún tiene que llegar a él)
                    if camino:
                        mi_auto.ruta = camino
                        mapa.camino_resaltado = camino # Actualizar dibujo verde

                # CASO B: El auto está quieto (Selección Origen -> Destino normal)
                else:
                    if seleccion_origen is None:
                        seleccion_origen = nodo_clicado
                        print(f"Origen seleccionado: {seleccion_origen}")
                        mapa.camino_resaltado = [seleccion_origen]
                    else:
                        seleccion_destino = nodo_clicado
                        print(f"Destino seleccionado: {seleccion_destino}")
                        
                        camino = mapa.dijkstra(seleccion_origen, seleccion_destino)
                        
                        if camino:
                            mi_auto.planificar_ruta(camino) # Aquí sí usamos el método normal con pop()
                            # Teletransportamos el auto al inicio para que empiece limpio
                            mi_auto.pos = list(mapa.nodos[seleccion_origen]) 
                        
                        # Reseteamos variables de selección
                        seleccion_origen = None
                        seleccion_destino = None

        # --- CLIC DERECHO (GESTIONAR OBSTÁCULOS) ---
        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 3:
            mouse_pos = pygame.mouse.get_pos()
            
            # 1. ¿Hice clic sobre un obstáculo existente? (Para borrarlo)
            obstaculo_a_eliminar = None
            for obs in lista_obstaculos:
                # Calculamos distancia al clic
                dx = mouse_pos[0] - obs.pos[0]
                dy = mouse_pos[1] - obs.pos[1]
                dist = (dx**2 + dy**2)**0.5
                
                if dist < obs.radio + 5: # +5 de margen para facilitar el clic
                    obstaculo_a_eliminar = obs
                    break
            
            # 2. Decidir acción
            if obstaculo_a_eliminar:
                lista_obstaculos.remove(obstaculo_a_eliminar)
                print("Obstáculo eliminado.")
            else:
                # Si no había nada, creamos uno nuevo
                nuevo_obs = Obstaculo(mouse_pos)
                lista_obstaculos.append(nuevo_obs)
                print(f"Obstáculo creado en {mouse_pos}")

    # 2. Actualización (Lógica)
    # Actualizar semáforos
    for s in semaforos:
        s.update()
    # Mover los NPCs
    for npc in lista_npcs:
        npc.update()

    # --- TRUCO DE FUSIÓN ---
    # Creamos una lista temporal que une rocas estáticas + autos en movimiento
    # Como ambos tienen atributo ".pos", el sensor del auto funcionará igual.
    obstaculos_totales = lista_obstaculos + lista_npcs
        
    # Actualizar auto (¡OJO! AHORA LE PASAMOS LOS SEMÁFOROS TAMBIÉN)
    mi_auto.update(mapa.nodos, semaforos, obstaculos_totales)

    # 3. Dibujado
    pantalla.fill(NEGRO)
    mapa.dibujar(pantalla)
    mi_auto.dibujar(pantalla)
    for s in semaforos:
        s.dibujar(pantalla)
    for obs in lista_obstaculos:
        obs.dibujar(pantalla)
    for npc in lista_npcs:
        npc.dibujar(pantalla)

    pygame.display.flip()
    reloj.tick(60)