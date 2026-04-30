# Guía de uso

## Lanzar una sesión

### Comando básico

Con la configuración preparada según la [Guía de instalación](install.md):

```bash
perssim-launch --session ./session.config.json
```

El launcher realiza automáticamente:

1. Leer y validar `session.config.json`.
2. Levantar un proceso independiente por cada personaje definido en `characters`.
3. Levantar el proceso orquestador (puerto 5000).
4. Esperar a que todos los puertos estén listos (health-check via `/status`).
5. Enviar a cada personaje su `initial_situation` personalizada via `/listen` y arrancar el primer turno via `/start_turns` en el orquestador.
6. El launcher termina; los procesos de personaje y orquestador siguen corriendo de forma independiente.

### Opciones del comando

| Opción | Descripción |
|---|---|
| `--session PATH` | Ruta al fichero `session.config.json`. Requerido. |
| `--log-level LEVEL` | Nivel de log: `DEBUG`, `INFO`, `WARNING`. Por defecto: `INFO`. |

---

## Interacción durante la sesión

El orquestador expone una interfaz de terminal (TUI) mientras corre. Se muestra en la consola donde se levantó el proceso orquestador.

### Comandos del sistema

Empiezan por `/`:

| Comando | Descripción |
|---|---|
| `/next` | Fuerza el paso al siguiente turno definido en `turn_order`. |
| `/next <id>` | Fuerza el turno directamente al personaje indicado. |
| `/wait` | Pausa la sesión al terminar el turno actual. Los personajes no reciben más `/turn` hasta `/continue`. |
| `/continue` | Reanuda la sesión desde donde se pausó. |
| `/turn-status` | Muestra turno actual, personaje activo, orden de turnos, deadline y si está pausado. |

### Intervención del narrador

Cualquier texto que **no empiece por `/`** se envía como narración a todos los personajes y se registra en el log.

```
Ha llegado un mensajero de Madrid con noticias urgentes.
```
```
El rey ha convocado consejo para mañana al amanecer.
```

> El narrador es tu herramienta principal para guiar el diálogo. Los personajes integran los mensajes del narrador en su historial como contexto de usuario.

---

## Ejemplo de sesión

```
[14:30:00] NARRADOR a Todos:
Es invierno de 1635. Richelieu y Mazarino debaten en privado la posición de Francia.

──────────────────────────────────────────────────
[14:31:12] #001 RICHELIEU a Todos:
Monsieur Mazarino, os he llamado para que me digáis con franqueza: ¿puede el
Rey de España sostener dos frentes simultáneamente sin quebrar su hacienda?
──────────────────────────────────────────────────

──────────────────────────────────────────────────
[14:32:44] #002 MAZARIN a Todos:
Eminencia, los informes de Milán confirman que el tesoro castellano lleva tres
años en déficit. Pero sería un error subestimar la tenacidad de Olivares.
──────────────────────────────────────────────────
```

El usuario escribe en la consola del orquestador:

```
Ha llegado un correo de Roma. El Papa pide a Francia que cese las hostilidades.
```

```
──────────────────────────────────────────────────
[14:35:10] NARRADOR a Todos:
Ha llegado un correo de Roma. El Papa pide a Francia que cese las hostilidades.
──────────────────────────────────────────────────

──────────────────────────────────────────────────
[14:36:02] #003 RICHELIEU a Todos:
Las consideraciones espirituales son siempre bienvenidas. Pero la seguridad del
reino no puede supeditarse a negociaciones que los Habsburgo usarán para ganar tiempo.
──────────────────────────────────────────────────
```

---

## El fichero de log

Cada sesión genera un fichero de log en texto plano en la ruta indicada en `session.config.json`. Se añade sufijo numérico automático (`-0001`, `-0002`…) para no sobreescribir logs anteriores.

Formato de cada entrada:

```
21/04/2026 - 14:31
De Richelieu a Todos
Monsieur Mazarino, os he llamado...

21/04/2026 - 14:32
De Mazarin a Todos
Eminencia, los informes de Milán...
```

### Log de debug Ollama

Si `ollama_debug: true` en `session.config.json`, se genera un fichero JSON adicional con todas las peticiones y respuestas al API de Ollama, útil para depuración:

```json
[
  {
    "ts": "2026-04-21T14:31:12Z",
    "who": "richelieu",
    "direction": "request",
    "model": "llama3",
    "system": "...",
    "messages": [
      { "role": "user", "content": "narrador: Es invierno de 1635..." }
    ]
  },
  {
    "ts": "2026-04-21T14:31:30Z",
    "who": "richelieu",
    "direction": "response",
    "content": "Monsieur Mazarino..."
  }
]
```

---

## Resolución de problemas

| Problema | Solución |
|---|---|
| El personaje no responde | Verifica que Ollama está corriendo y que el modelo en `char.config.json` está descargado (`ollama list`). |
| El personaje responde fuera de su época | Usa `Bundle_narrative` en lugar de `Bundle_strict`. Los modelos <7B respetan menos las restricciones temporales. |
| Error de puerto en uso | Cambia los puertos en `session.config.json` y `chars/*.config.json`. |
| Timeout frecuente | Aumenta `turn_timeout_seconds` en `session.config.json`. Modelos grandes pueden tardar >60s en hardware modesto. |
| El historial se hace muy largo | Reduce `max_character_history` para limitar el contexto enviado a Ollama. |
| El personaje mezcla voces | Verifica que el Bundle incluye instrucciones de rol claras. Usa `Bundle_narrative` con modelos más pequeños. |
