import random
import threading  # Para crear un hilo por vehiculo, el Lock y el Event
import time       # time.sleep() pausa SOLO el hilo del vehiculo, no la ventana
import tkinter as tk

class Vehiculo:
    reduccion = 8
    ancho = 59
    paso = 4
    intervaloMin = 10
    intervaloMax = 40

    def __init__(self, numero, nombre, canvas, y, xMin, xMax, obtenerEscala, alTerminar):
        self.numero = numero
        self.nombre = nombre
        self.canvas = canvas
        self.y = y
        self.xMin = xMin
        self.xMax = xMax
        self.obtenerEscala = obtenerEscala
        self.alTerminar = alTerminar
        self.tag = f"vehiculo{numero}"
        self.tagInfo = f"info{numero}"
        self.imagen = tk.PhotoImage(file="car.png").subsample(self.reduccion)

        # Lock: candado que protege x, direccion, rondas, etc. Esos datos los
        # escribe el hilo del vehiculo y los lee la ventana para dibujar, asi
        # que solo uno de los dos puede tocarlos a la vez.
        self.lock = threading.Lock()
        # Event: senal para avisarle al hilo que debe parar (al reiniciar).
        self.eventoDetener = threading.Event()
        # El hilo se crea en iniciar(); un Thread solo se puede arrancar una
        # vez, por eso se crea uno nuevo en cada carrera.
        self.hilo = None
        # Milisegundos que espera el hilo entre cada paso (menos = mas rapido).
        self.intervaloMs = self.intervaloMax

        self.canvas.create_text(10, y - 8, anchor="w", text=nombre, font=("Arial", 9, "bold"))
        self.canvas.create_text(10, y + 9, anchor="w", text="", font=("Arial", 8), tags=self.tagInfo)
        self.canvas.create_image(xMin, y, anchor="w", image=self.imagen, tags=self.tag)
        self.reiniciar()

    def reiniciar(self):
        # Primero se detiene el hilo para que no siga moviendo el carro
        # mientras se reinician sus datos.
        self.detener()
        with self.lock:
            self.x = self.xMin
            self.direccion = 1
            self.rondasCompletadas = 0
            self.rondasObjetivo = 0
            self.terminado = False
            self.tiempoFinal = None
        self.dibujar()
        self.actualizarInfo()

    def iniciar(self, rondas):
        self.rondasObjetivo = rondas
        self.cambiarVelocidad()
        # Se baja la senal de detener por si quedo activa de la carrera anterior.
        self.eventoDetener.clear()
        # Se crea el hilo de ESTE vehiculo: ejecutara correr() por su cuenta.
        # daemon=True: si se cierra la ventana, el hilo muere con el programa.
        self.hilo = threading.Thread(target=self.correr, name=self.nombre, daemon=True)
        self.hilo.start()

    def detener(self):
        # set() levanta la senal; el ciclo de correr() la ve y termina.
        self.eventoDetener.set()
        if self.hilo is not None:
            # join() espera a que el hilo termine de verdad antes de seguir.
            self.hilo.join()
            self.hilo = None

    # Esto es lo que ejecuta el hilo del vehiculo (reemplaza al Temporizador).
    # Corre en paralelo con los otros 9 hilos y con la ventana.
    def correr(self):
        while not self.eventoDetener.is_set():
            # Espera el intervalo del vehiculo, dividido por la escala del
            # slider: escala 2 -> espera la mitad -> el carro va el doble de rapido.
            time.sleep(self.intervaloMs / 1000 / self.obtenerEscala())
            # Si mientras dormia se pidio detener (Reiniciar), sale sin mover.
            if self.eventoDetener.is_set():
                return
            # mover() devuelve True cuando el carro completo todas sus rondas.
            if self.mover():
                # Avisa a la interfaz que llego a la meta y el hilo termina.
                self.alTerminar(self)
                return

    def cambiarVelocidad(self):
        self.intervaloMs = random.randint(self.intervaloMin, self.intervaloMax)

    def velocidad(self):
        return self.paso * 1000 / self.intervaloMs

    # Lo llama el hilo del vehiculo. Solo calcula la nueva posicion; NO dibuja,
    # porque Tkinter solo se puede tocar desde el hilo principal.
    def mover(self):
        # Se toma el candado para que la ventana no lea x a medio actualizar.
        with self.lock:
            self.x += self.paso * self.direccion

            if self.direccion == 1 and self.x >= self.xMax:
                self.x = self.xMax
                self.direccion = -1
                self.cambiarVelocidad()

            elif self.direccion == -1 and self.x <= self.xMin:
                self.x = self.xMin
                self.rondasCompletadas += 1
                if self.rondasCompletadas >= self.rondasObjetivo:
                    self.terminado = True
                    return True
                self.direccion = 1
                self.cambiarVelocidad()
        return False

    # Lo llama la ventana (hilo principal). Lee los datos con el candado y
    # despues actualiza el texto del carril.
    def actualizarInfo(self):
        with self.lock:
            if self.terminado:
                texto = f"Meta! ({self.rondasCompletadas}/{self.rondasObjetivo})"
            elif self.rondasObjetivo == 0:
                texto = "En parrilla"
            else:
                texto = f"Ronda {self.rondasCompletadas + 1}/{self.rondasObjetivo}  {self.velocidad():.0f} px/s"
        self.canvas.itemconfig(self.tagInfo, text=texto)

    # Lo llama la ventana (hilo principal): copia x con el candado y mueve
    # la imagen del carro a esa posicion.
    def dibujar(self):
        with self.lock:
            x = self.x
        self.canvas.coords(self.tag, x, self.y)
