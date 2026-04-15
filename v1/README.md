El modelo de capas propuesto
Basándonos en la Teoría de Valores de Schwartz, la jerarquía de necesidades, el modelo BDI y las arquitecturas cognitivas ACT-R y CLARION, proponemos una arquitectura de decisión en cinco capas:

Capa	Concepto psicológico	Contenido	Velocidad de cambio
1. Valores nucleares	Schwartz / Moral Foundations	Principios morales y motivacionales más profundos. Casi inmutables.	Décadas
2. Necesidades activas	Maslow / homeostasis	Estado de satisfacción de necesidades básicas: supervivencia, seguridad, afiliación, estima.	Días / semanas
3. Metas e intereses	BDI Desires / Goals	Objetivos a medio-largo plazo: poder, riqueza, reconocimiento, legado.	Meses / años
4. Disposiciones situacionales	Big Five + Emociones	Rasgos que modulan cómo se persiguen las metas: estilo comunicativo, reactividad emocional.	Estable en adultos
5. Respuestas contextuales	BDI Intentions + Plans	Decisión final en una situación concreta, tras filtrar por las capas anteriores.	Segundos / minutos
El flujo decisional es top-down con feedback bottom-up: una situación activa la Capa 5, que consulta las disposiciones de la Capa 4, que a su vez selecciona entre las metas de la Capa 3 la más compatible con los valores de la Capa 1 y el estado de necesidades de la Capa 2.

Cómo funciona el filtrado jerárquico
Imaginemos a un personaje histórico con los siguientes parámetros:

Capa 1 (Valores): Honor y Lealtad al grupo > Poder personal > Benevolencia
Capa 2 (Necesidades): Seguridad personal amenazada, afiliación grupal alta
Capa 3 (Metas): Ascender políticamente, proteger a su familia, mantener su reputación
Capa 4 (Disposiciones): Alta Responsabilidad, baja Amabilidad, alta Extraversión
Capa 5 (Situación): Se le ofrece aliarse con el enemigo de su señor a cambio de tierras
El proceso decisional sería: La opción traicionar al señor choca con el valor de Lealtad (Capa 1), lo que genera tensión. La amenaza a la seguridad (Capa 2) hace la oferta atractiva. La meta de reputación (Capa 3) actúa como freno adicional a la traición. La alta Responsabilidad (Capa 4) refuerza el cumplimiento de compromisos previos. El resultado probable: rechaza la oferta pero negocia protección de otra manera.

Este es exactamente el tipo de razonamiento que un LLM puede simular de forma natural si se le proporciona el estado de cada capa como contexto estructurado. La clave es que las capas superiores actúan como restricciones que narran el espacio de opciones aceptables.

Prioridad dinámica: cuando las capas entran en conflicto
Schwartz demostró que los valores no son aditivos sino que compiten en un continuum circular. Un individuo con alto valor de Logro personal y alto valor de Benevolencia experimentará tensión permanente. La resolución de este conflicto define el carácter del personaje más que sus valores individuales.

Para implementar esto computacionalmente, se pueden usar dos mecanismos: un vector de prioridades ordenadas (qué valor «gana» cuando hay conflicto explícito) y un sistema de umbrales de activación (un valor se activa cuando la situación lo hace relevante y su activación supera un umbral).

Recomendaciones para el modelo de datos
A partir de todo lo anterior, proponemos un modelo de datos en cuatro bloques que puede servir como base para tus simulaciones históricas, complementándose con el corpus biográfico. El modelo está diseñado para ser legible por humanos, procesable por LLMs como contexto y extensible.

Estructura recomendada del modelo de datos
El formato recomendado es JSON Schema, por tres razones: es nativo para LLMs (fueron entrenados con enormes cantidades de JSON), soporta validación estructural, y puede inyectarse directamente en el system prompt. A continuación, la estructura de cuatro bloques:

Bloque 1: Identidad y contexto histórico
Captura quién es el personaje en su mundo:

{  "id": "cardinal_richelieu_1625",  "nombre": "Armand Jean du Plessis de Richelieu",  "nacimiento": 1585,  "muerte": 1642,  "contexto_historico": {    "epoca": "Francia del Ancien Régime",    "cargo": "Primer Ministro de Luis XIII",    "clase_social": "Nobleza eclesiástica"  },  "identidades_de_grupo": [    { "grupo": "Iglesia Católica", "rol": "Cardenal", "lealtad": 0.7 },    { "grupo": "Corona Francesa", "rol": "Servidor del Rey", "lealtad": 0.9 },    { "grupo": "Nobleza francesa", "rol": "Miembro", "lealtad": 0.5 }  ] }
Bloque 2: Perfil de personalidad (Big Five)
Valores continuos de 0.0 a 1.0, con facetas opcionales para mayor granularidad:

"personalidad": {  "OCEAN": {    "apertura":        0.65,    "responsabilidad": 0.92,    "extraversion":    0.55,    "amabilidad":      0.28,    "neuroticismo":    0.35  },  "facetas_notables": [    "Maquiavélico en medios, idealista en fines",    "Alta tolerancia a la ambigüedad moral",    "Pragmatismo extremo ante la necesidad política"  ] }
Bloque 3: Jerarquía de valores y motivaciones
El corazón del sistema de decisiones. Los valores están ordenados por prioridad e incluyen posibles conflictos conocidos:

"valores_y_motivaciones": {  "valores_nucleares": [    { "valor": "Poder del Estado francés",   "prioridad": 1, "notas": "Fin último que justifica casi cualquier medio" },    { "valor": "Lealtad a la Corona",         "prioridad": 2, "notas": "Instrumental, no sentimental" },    { "valor": "Fe católica",                 "prioridad": 3, "notas": "Sincera pero subordinada a la razón de Estado" },    { "valor": "Supervivencia y poder propio","prioridad": 4, "notas": "Necesario para ejercer los anteriores" }  ],  "necesidades_activas": {    "seguridad": 0.6,    "poder_e_influencia": 0.95,    "reconocimiento": 0.75  },  "metas_vitales": [    "Centralizar el poder en la monarquía",    "Reducir el poder de la nobleza huguenote",    "Construir un legado duradero como estadista"  ],  "conflictos_internos": [    "Fe vs. alianzas con protestantes cuando conviene al Estado",    "Lealtad al Rey vs. necesidad de actuar con autonomía"  ] }
Bloque 4: Patrones de comportamiento y estilo
Reglas y tendencias que guían la expresión situacional de la personalidad:

"comportamiento": {  "estilo_comunicativo": "Formal, indirecto, calculado. Raramente expresa opiniones sin calcular el efecto",  "manejo_del_conflicto": "Prefiere maniobras diplomáticas a la confrontación directa. Si cornered, implacable",  "relaciones_interpersonales": {    "confia_en": ["muy pocas personas cercanas, probadas con el tiempo"],    "actitud_hacia_subordinados": "Instrumental, pero reconoce y recompensa la competencia"  },  "lineas_rojas": [    "No traicionará al Rey directamente mientras sea políticamente viable",    "Nunca admitirá debilidad en público"  ],  "sesgos_cognitivos": [    "Tiende a interpretar las acciones ajenas en términos de interés político",    "Subestima el factor emocional en las decisiones de otros"  ] }
Cómo integrar este modelo con el corpus biográfico
El modelo de datos es la estructura; el corpus biográfico (cartas, discursos, memorias, biografías) es el contenido que lo rellena y valida. La integración recomendada es la siguiente:

Nivel 1 — Extracción: usa un LLM para analizar el corpus y proponer valores iniciales para cada campo del JSON. Esto es un proceso asistido que requiere revisión humana.
Nivel 2 — Validación cruzada: contrasta los valores propuestos con evidencia biográfica concreta. Cada valor del JSON debería poder citarse con al menos una fuente primaria.
Nivel 3 — Inyección en contexto: el JSON completo se convierte en el system prompt del agente, junto con un extracto relevante del corpus (las cartas o textos más representativos del período simulado).
Nivel 4 — Memoria episódica: para simulaciones largas, los eventos de la conversación se añaden a una memoria vectorial que complementa el JSON estructurado con experiencias específicas.
La investigación de Park et al. (2024) confirma que un transcript biográfico completo en contexto supera a los agentes basados solo en descripciones demográficas o de rasgos. La combinación JSON + extractos biográficos + memoria episódica es el estado del arte.

Recomendaciones técnicas de implementación
Formato de almacenamiento

JSON Schema con validación estricta es la opción óptima. Permite validar que el modelo está completo antes de inyectarlo, es directamente legible por el LLM, y puede versionarse en git. Para colecciones de personajes, una base de datos de documentos como MongoDB o PostgreSQL con soporte JSONB es adecuada.

Inyección en el LLM

El modelo de datos debe incluirse íntegro en el system prompt, precedido de instrucciones que indiquen al LLM cómo interpretarlo. La estructura recomendada del system prompt es:

Sección 1: Instrucción de rol («Eres [nombre]. Adopta este personaje completamente. Tu personalidad, valores y decisiones deben ser coherentes con el siguiente perfil»)
Sección 2: El JSON del personaje, con cada bloque claramente etiquetado.
Sección 3: Extracto biográfico seleccionado (cartas, discursos propios del período).
Sección 4: Instrucciones de restricción temporal («Solo tienes conocimiento de eventos hasta [fecha]. Si se te pregunta sobre algo posterior, reacciona con la perspectiva de tu época»).
Modelo de datos para la jerarquía de decisiones en tiempo de inferencia

Para que el LLM tome decisiones coherentes ante dilemas, se puede añadir un paso de razonamiento explícito en cadena (chain-of-thought) que recorra las cinco capas antes de generar la respuesta:

Antes de responder a esta situación, razona internamente: 1. ¿Esta acción entra en conflicto con mis valores nucleares? (Capa 1) 2. ¿Qué necesidades mías están en juego en este momento? (Capa 2) 3. ¿Cómo afecta esta acción a mis metas vitales? (Capa 3) 4. ¿Cómo reaccionaría típicamente alguien con mi personalidad? (Capa 4) 5. Dada la situación concreta, ¿cuál es mi respuesta más auténtica? (Capa 5)

Herramientas y frameworks recomendados

Componente	Herramienta recomendada	Alternativa
Almacenamiento de personajes	PostgreSQL + JSONB	MongoDB
Memoria episódica	Vector DB (Pinecone, Weaviate, pgvector)	ChromaDB (local)
Orquestación del agente	LangChain / LlamaIndex	Código propio con Anthropic API
Modelo base	Claude Sonnet 4 / GPT-4o	Llama 3.3 70B (local)
Validación del JSON	JSON Schema + Pydantic	Zod (TypeScript)
Versionado de personajes	Git + archivos .json	Notion / Airtable
Advertencias y límites del sistema
Es importante ser consciente de las limitaciones conocidas antes de confiar plenamente en el sistema:

Deriva de carácter: en conversaciones largas, los LLMs tienden a suavizar los rasgos extremos y converger hacia un perfil más «agradable». Solución: incluir recordatorios periódicos del perfil en el contexto.
Anachronismo involuntario: el LLM puede introducir perspectivas modernas aunque el personaje no las tendría. Las «Protective Experiences» del método Character-LLM y las instrucciones explícitas de restricción temporal ayudan.
Coherencia vs. sorpresa: un perfil muy rígido puede hacer al personaje predecible. Los valores de Schwartz modelan bien la tensión interna que genera comportamientos inesperados pero explicables a posteriori.
Validación: no existe aún una métrica estándar para evaluar la «fidelidad histórica» de una simulación. Se recomienda un protocolo de evaluación mixto: test de escenarios históricos documentados + revisión experta.
Hoja de ruta de implementación
Para un proyecto de simulación histórica, recomendamos la siguiente secuencia:

Fase 1 — Piloto (1-2 meses): Define un personaje bien documentado. Construye el JSON manualmente a partir del corpus biográfico. Implementa el sistema de prompts en capas. Evalúa con 20-30 escenarios históricos conocidos.
Fase 2 — Extracción asistida (2-4 meses): Desarrolla un pipeline que use el LLM para proponer borradores del JSON a partir del corpus, con revisión humana. Construye la biblioteca de personajes.
Fase 3 — Memoria episódica (3-6 meses): Integra una base de datos vectorial para memoria a largo plazo. Implementa el razonamiento en cadena de cinco capas como rutina estándar.
Fase 4 — Evaluación y refinamiento continuo: Protocolo de evaluación con historiadores o expertos. Iteración del modelo de datos basada en los errores detectados.
Conclusiones
El estado actual de la psicología y la IA ofrece herramientas sólidas para construir agentes que simulen personalidades históricas de forma coherente. El punto clave es que ningún marco único es suficiente: la personalidad necesita el Big Five para describir el cómo, los valores de Schwartz para explicar el por qué, la jerarquía de necesidades para capturar el ahora, y el modelo BDI para estructurar el proceso de decisión.

La investigación más reciente confirma que el corpus biográfico en contexto es el factor más determinante de la fidelidad de la simulación, superando a las descripciones de rasgos abstractas. Tu enfoque de combinar un modelo de datos estructurado con material biográfico está alineado con el estado del arte.

El modelo de datos propuesto en cuatro bloques (Identidad, Personalidad OCEAN, Valores y Motivaciones, Comportamiento) ofrece una base formal que el LLM puede interpretar directamente, mientras que la arquitectura de decisión en cinco capas proporciona el marco para que las respuestas del agente sean coherentes con la lógica interna del personaje, no solo con la superficie de su historia.
