# Guía de uso

## Lanzar una sesión

### Comando básico

Con la configuración preparada según la [Guía de instalación](install.md):

```bash
persim-launch --session ./session.json
```

El iniciador realizará automáticamente:

1. Leer `session.json` y validar la configuración.
2. Levantar un proceso `CharXXX` por cada personaje definido.
3. Levantar el proceso Orquestador.
4. Esperar a que todos los puertos estén listos (health-check).
5. Enviar la situación inicial a todos los personajes.
6. Abrir la interfaz de terminal.

### Opciones del comando

| Opción | Descripción |
|---|---|
| `--session PATH` | Ruta al fichero `session.json`. Requerido. |
| `--init DIR` | Crea un directorio de sesión con ficheros de ejemplo. No lanza la sesión. |
| `--port INT` | Puerto del orquestador. Por defecto: 5000. |
| `--no-tui` | Lanza sin interfaz de terminal. Útil para pruebas o scripting. |
| `--log-level` | Nivel de log del sistema: `debug`, `info`, `warning`. Por defecto: `info`. |

---

## Interfaz de terminal

La pantalla tiene dos paneles:

- **Panel superior** (80%): diálogo en tiempo real, con nombre del personaje, destinatario y mensaje.
- **Panel inferior** (20%): campo de entrada de comandos del usuario.

Formato de cada intervención:

```
[14:32:01] RICHELIEU → MAZARINO
Monsieur Mazarino, la situación en los Países Bajos exige...
```

Cuando el mensaje va dirigido a todos, el destinatario aparece como `TODOS`.

Los mensajes del narrador se muestran diferenciados:

```
[14:35:10] NARRADOR → TODOS
Ha llegado un mensajero de Madrid con noticias urgentes.
```

Pulsa `Ctrl+L` en cualquier momento para refrescar la pantalla si la TUI se corrompe visualmente.

---

## Comandos durante la sesión

### Comandos del sistema

Empiezan por `/`:

| Comando | Descripción |
|---|---|
| `/wait` | Congela todos los personajes. El diálogo se detiene. |
| `/continue` | Reanuda todos los personajes. |
| `/talk <id>` | Fuerza una intervención inmediata del personaje indicado. |
| `/restart <id>` | Reinicia un personaje (útil al cambiar de modelo). Preserva el historial. |
| `/status` | Estado de cada personaje: activo, en pausa, último turno, modelo en uso. |
| `/log` | Muestra la ruta del fichero de log activo. |
| `/quit` | Cierra la sesión ordenadamente. Todos los procesos terminan y el log queda guardado. |

### Intervención del narrador

Cualquier texto que **no empiece por `/`** se envía como mensaje del narrador a todos los personajes. Los personajes lo reciben y deciden si intervienen y qué dicen.

Ejemplos de uso:

```
Ha llegado un mensajero de Madrid con noticias urgentes.
```
```
El rey ha convocado consejo para mañana al amanecer.
```
```
Richelieu, el Papa os ha enviado una misiva.
```

> El narrador es tu herramienta principal para guiar el diálogo sin interrumpirlo. Los personajes interpretan los mensajes del narrador en el contexto de su época y personalidad.

---

## Ejemplo de sesión

```
[14:30:00] NARRADOR → TODOS
Es invierno de 1635. Richelieu y Mazarino debaten en privado la posición de Francia.

[14:31:12] RICHELIEU → MAZARINO
Monsieur Mazarino, os he llamado para que me digáis con franqueza: ¿puede el
Rey de España sostener dos frentes simultáneamente sin quebrar su hacienda?

[14:32:44] MAZARINO → TODOS
Eminencia, los informes de Milán confirman que el tesoro castellano lleva tres
años en déficit. Pero sería un error subestimar la tenacidad de Olivares.
```

El usuario escribe en el panel inferior:

```
Ha llegado un correo de Roma. El Papa pide a Francia que cese las hostilidades.
```

```
[14:35:10] NARRADOR → TODOS
Ha llegado un correo de Roma. El Papa pide a Francia que cese las hostilidades.

[14:36:02] RICHELIEU → TODOS
Las consideraciones espirituales son siempre bienvenidas. Pero la seguridad del
reino no puede supeditarse a negociaciones que los Habsburgo usarán para ganar
tiempo.
```

---

## Cambiar el modelo LLM durante una sesión

1. `/wait` — congela la sesión.
2. Edita `chars/<personaje>.json` y cambia `ollama_model`.
3. `/restart <id>` — reinicia ese personaje con el nuevo modelo. El historial se preserva.
4. `/continue` — reanuda la sesión.

---

## El fichero de log

Cada sesión genera un fichero JSONL en la ruta indicada en `session.json`:

```jsonl
{ "ts": "2025-01-15T14:32:01Z", "who": "richelieu", "to": ["mazarin"], "message": "Monsieur Mazarino..." }
{ "ts": "2025-01-15T14:33:15Z", "who": "mazarin", "to": [], "message": "Eminencia, los informes..." }
```

Lectura y filtrado:

```bash
# Ver el diálogo completo con formato
cat logs/sesion_001.jsonl | python -m json.tool

# Solo las intervenciones de un personaje
grep '"who": "richelieu"' logs/sesion_001.jsonl
```

> El log puede usarse para actualizar la memoria de los personajes en PerSSim mediante el comando `/Memoria`, alimentando futuras sesiones con los eventos ocurridos.

---

## Resolución de problemas

| Problema | Solución |
|---|---|
| El personaje no responde | Verifica que Ollama está corriendo y que el modelo indicado en `char.json` está descargado. Usa `/status`. |
| El personaje responde fuera de su época | Prueba `Bundle_narrative` en lugar de `Bundle_strict`. Los modelos <7B respetan menos las restricciones temporales. |
| Error de puerto en uso | Cambia los puertos en `session.json` y `chars/*.json`. Los puertos 5000-5099 están libres por defecto. |
| La TUI se corrompe visualmente | Pulsa `Ctrl+L` para refrescar. Si persiste, lanza con `--no-tui` y lee el log directamente. |
| Timeout en respuesta de Ollama | Aumenta `wait_min_seconds` en `char.json` para dar más margen entre intervenciones. |
