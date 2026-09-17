"""Worker del agente de Agilina.

Proceso de larga vida sin interfaz ni puerto de entrada: al arrancar abre una
conexión de salida hacia LiveKit y se registra como trabajador disponible.
Cuando se crea la sala de una ceremonia, LiveKit ofrece el trabajo por esa
conexión ya abierta y el worker lanza un subproceso dedicado a esa sala. Nunca
necesita ser accesible desde internet.
"""

__version__ = "0.1.0"
