import threading
import time

class Cronometro:

    def __init__(self):
        self.tiempoInicio = None
        self.tiempoAcumulado = 0.0
        self.escala = 1.0
        # Candado: el cronometro lo leen los 10 hilos de los vehiculos (al
        # llegar a la meta) y la ventana (reloj y slider) al mismo tiempo.
        # Es RLock (reentrante) porque detener() llama a tiempoTranscurrido()
        # y ambos toman el candado; un Lock normal se bloquearia a si mismo.
        self.lock = threading.RLock()

    def iniciar(self):
        with self.lock:
            self.tiempoAcumulado = 0.0
            self.tiempoInicio = time.perf_counter()

    def cambiarEscala(self, nuevaEscala):
        with self.lock:
            if self.tiempoInicio is not None:
                ahora = time.perf_counter()
                self.tiempoAcumulado += (ahora - self.tiempoInicio) * self.escala
                self.tiempoInicio = ahora
            self.escala = nuevaEscala

    def tiempoTranscurrido(self):
        with self.lock:
            if self.tiempoInicio is None:
                return self.tiempoAcumulado
            return self.tiempoAcumulado + (time.perf_counter() - self.tiempoInicio) * self.escala

    def detener(self):
        with self.lock:
            self.tiempoAcumulado = self.tiempoTranscurrido()
            self.tiempoInicio = None
            return self.tiempoAcumulado

    def reiniciar(self):
        with self.lock:
            self.tiempoInicio = None
            self.tiempoAcumulado = 0.0
