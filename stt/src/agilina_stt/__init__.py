"""Servicio de transcripción de Agilina.

Convierte segmentos de audio en texto. No identifica hablantes: la identidad
llega con la pista de audio, firmada en el token de LiveKit. Vive en su propia
instancia porque necesita GPU, es el componente más caro por hora y debe poder
encenderse y apagarse con la ceremonia sin afectar al resto.
"""

__version__ = "0.1.0"
