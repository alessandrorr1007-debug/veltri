# Capa cognitiva y agentes — FASE 6

Ocho agentes independientes con contratos previos al código, BaseAgent y fábrica
única get_llm. Los nombres y funciones fueron confirmados por el usuario. No hay
grafo, API ni interfaz; los nodos en docs/agentes/ son integración futura.

## Responsabilidades
D1: A1 interpreta intención; A2 arma por rango; A3 cotiza una selección.
D2: A4 comprueba compatibilidad. D3: A5 comprueba stock y ofrece alternativas.
D4: A6 compara importes, A7 registra borradores y A8 consulta su estado.
Cada agente tiene módulo, prompt propio y diagrama en docs/agentes/.
A8 no despacha ni representa un servicio logístico.

## Configuración y fábrica
src/config.py lee .env (sin interpolación) y variables del proceso, que tienen
prioridad. USE_MOCK_LLM debe ser 1 o 0; por defecto es 1. LLM_PROVIDER admite gemini.
LLM_MODEL nunca se fija a un modelo comercial en código. En modo real se requieren
LLM_MODEL y GOOGLE_API_KEY; esta clave usa SecretStr, no aparece en repr ni
model_dump de Configuracion. No serializar configuración ni excepciones crudas.
Solo core/llm.py construye MockLLM o el cliente del proveedor mediante get_llm.

MockLLM consume una cola de respuestas de prueba explícitas y validadas; no guarda
prompts, no infiere intenciones ni consulta servicios. Agotar las respuestas o
recibir JSON fuera del contrato produce ErrorModelo con código fijo. No hay
fallback silencioso que invente una clasificación.

GeminiLLM usa el SDK oficial google-genai, interfaz interactions, modelo de la
configuración, salida JSON Schema, timeout de petición y store=False. El modo
Vertex está desactivado explícitamente. El plan se valida de nuevo con Pydantic.
No se habilitan herramientas remotas, navegación ni ejecución de código. store=False
solicita no conservar el historial de la interacción; no es una garantía general
sobre retención del proveedor. Esta entrega NO hizo consultas reales ni gastó cuota.
Las pruebas del conector usan el SDK instalado con transporte simulado; no prueban
que un modelo particular admita el esquema o que una cuenta tenga acceso.
Referencia: [salidas estructuradas de Gemini](https://ai.google.dev/gemini-api/docs/structured-output).

Dependencias directas nuevas: google-genai 2.31.0 para el conector y python-dotenv
1.2.4 para leer .env (ya transitiva en el entorno). requirements-fase6.txt incluye
las fases previas. pip ajustó dependencias transitivas compatibles; pip check debe
seguir pasando. No se instalaron LangGraph ni LangChain para esta fase.

## Contratos y límites del modelo
PlanModelo solo permite accion (enum), p y c entre 0 y 1. No admite precios,
stock, cantidades, tenant, clientes, aprobaciones, texto de enrutamiento o cifras
de cuello de botella. BaseAgent rechaza un plan fuera de su dominio antes de
llamar herramientas. Cada entrada se revalida, incluidos campos mutables.
Las excepciones públicas del modelo/agente usan códigos fijos; errores de
parámetros de herramientas no se repiten como texto recibido del cliente.

A1 recibe ConsultaRequest, filtra el mensaje y propone intención; no extrae
montos, no convierte soles a céntimos ni compone pedidos a partir de prosa.
A2–A8 reciben parámetros tipados explícitos y envían al modelo solo una descripción
mínima de la tarea: sin precios, importes, selección, alias de cliente o tenant.
Las herramientas utilizan los parámetros originales validados del llamador,
nunca argumentos generados por el modelo. Los agentes calculan resultados de demo
mediante tools/; una evaluación alta no los convierte en resultados aprobados.

SalidaAgente contiene agente, tenant_id, plan, origen_puntuacion y resultado tipado.
El origen es prueba_no_calibrada para MockLLM o modelo_no_calibrado para Gemini.
Ninguno se presenta como una medición ni una probabilidad calibrada. Los planes
no ejecutan un grafo ni conceden autorización. La compuerta existente aún solo
admite el origen de prueba: no se conectan planes reales automáticamente a ella.
Para pruebas, la evidencia determinista de un agente puede pasarse explícitamente
a SolicitudDecision con origen de prueba; se prueba el agotado CP-3 con p alta.

A2 devuelve ResultadoArmado (incluida ausencia de PC dentro del rango).
A3 devuelve ResultadoCotizacion; A4, ResultadoTecnico; A5, ResultadoInventario
(stock y alternativas sin sustitución); A6, ResultadoPago no_conciliado.
A7 devuelve ResultadoPedido de borrador; A8, EstadoBorrador o ausencia explícita.
A1 tiene resultado null porque su salida útil es el plan de intención.
Los JSON Schema se exportan en docs/contratos/ (35 modelos en total).
ConsultaResponse y los contratos anteriores de decisión no cambian.

## Borradores, consentimiento y tenant
A7 exige confirmar_borrador=true (booleano estricto) del llamador. Eso solo expresa
consentimiento a crear un borrador sintético, no aceptación de una venta ni pago.
Un error de modelo ocurre antes de escribir. tools/registro.py particiona un
RegistroDemo por tenant con un bloqueo local por instancia, y A7/A8 comparten ese
servicio por inyección explícita del llamador. Sin tenant no operan. La fórmula
SHA-256 de pedido original cliente|productos|cantidad|canal se conserva; tenant
particiona el almacenamiento, sin alterar el hash ni añadir timestamps.
No hay pedido confirmado, reserva, conciliación bancaria ni despacho. El registro
está en memoria, no coordina procesos y no autentica clientes ni tenants.
No se transmiten al proveedor los alias sintéticos o claves de borrador.

## Seguridad y privacidad
core/seguridad.py añade una guarda previa al modelo para patrones comunes de PII
y de prompt injection en inglés/español. Un bloqueo devuelve un código sin eco del
mensaje, antes de consumir una respuesta del modelo. El conector real también
aplica la guarda si se invoca directamente. No hay logs propios con mensajes,
claves o respuestas. Las salidas de agentes no se indexan en RAG.

La guarda por patrones no detecta todas las inyecciones ni todos los formatos de
PII; no sustituye controles de autenticación, políticas de permisos o validación
de argumentos. El límite duro sigue siendo el contrato del plan y las herramientas
sin privilegios de confirmación. No se implementa ni se declara una DLQ durable;
CP-2 se prueba parcialmente como bloqueo previo, sin archivo en cola.

## Probar sin red ni cuota
```powershell
.\.venv\Scripts\python -m pip install -r requirements-fase6.txt
.\.venv\Scripts\Activate.ps1
python -m pytest tests/test_llm.py tests/test_agentes.py -q
python scripts/exportar_esquemas.py
python scripts/verificar.py
```

Ejemplo de A5 con fixture explícito:
```python
from src.agents.d3_inventario.a5_inventario import A5Inventario
from src.config import Configuracion
from src.schemas.agentes import EntradaSeleccion
from src.tools.catalogo import Catalogo

agente = A5Inventario(configuracion=Configuracion(), respuestas=[
    {"accion": "stock", "p": 1.0, "c": 1.0}
])
salida = agente.run(EntradaSeleccion(tenant_id="veltri_tecnologic_pe",
                    seleccion={"CPU-AMD-5500": 1}), Catalogo())
# salida.resultado.stock.hitl_requerido es true y hay alternativas con stock.
```

Los casos CP-1 a CP-7 no se modifican ni se declaran aprobados de extremo a extremo.
La línea base continúa vacía y protegida. Hay pruebas de agente por caso válido,
límite y fallo; grafo, preguntas para recopilar parámetros, composición de respuestas,
RAG generativo, calibración y autorización real quedan para fases posteriores.
