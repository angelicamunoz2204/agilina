# Decisiones arquitectónicas

Las decisiones AD-01 a AD-19 están en el documento de
arquitectura del Sprint 0. De aquí en adelante, cada decisión que cambie la
forma del sistema se registra como un archivo en esta carpeta, numerado y
enlazado desde el pull request que la aplica.

```
docs/adr/0020-titulo-corto.md
```

Una decisión entra aquí cuando cumple al menos una de estas condiciones:

- cambia un contrato entre desplegables;
- reemplaza un proveedor externo o el puerto que lo abstrae;
- cambia dónde vive un dato o quién es su fuente de verdad;
- descarta una alternativa que alguien volvería a proponer en seis meses.

Lo demás es implementación y se explica en el cuerpo del commit.

Una decisión cerrada no se borra ni se edita: se supersede con una nueva que la
referencia. El historial de por qué el sistema es como es vale más que la
pulcritud del archivo.
