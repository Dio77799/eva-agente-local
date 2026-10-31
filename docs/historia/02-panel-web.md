# Panel web
## Qué hicimos (técnico)
- Servidor con http.server de la stdlib (ThreadingHTTPServer para no congelarse en peticiones lentas como el chat).
- SPA ligera: una shell con barra lateral y un área que carga fragmentos por fetch a /seccion/<nombre> (whitelist por diccionario), navegación por hash, sin recargar.
- Estética terminal/CRT (fósforo verde, scanlines, glow, animaciones) de diseño propio; selector de tema (verde/azul/morado y dinámico que cicla).
- Todo el contenido dinámico se escapa con html.escape.
## Utilidad
- Operar Eva desde el navegador, 100% local (127.0.0.1), una sección a la vez y sin dependencias ni CDNs.
