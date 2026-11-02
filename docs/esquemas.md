# Contratos Pydantic

Contrato 1.0-demo utilizado por la aplicación. No cambia los
JSON de data/, evals/casos_dorados.json ni la salida de las herramientas.
No se modifica la línea base ni los umbrales. Son contratos de demostración,
no una declaración de funcionalidad productiva ni una versión definitiva de API.

## Archivos
- src/schemas/base.py: tipos estrictos, enteros, SKUs, fuentes y configuración común.
- entradas.py: ConsultaRequest, CotizacionRequest, ArmadoRequest,
  ComparacionPagoRequest y PedidoDemoRequest.
- resultados.py: líneas, stock, validación técnica, cotización, armado,
  comparación de importes y borradores idempotentes.
- consulta.py: ConsultaResponse (sobre de resultados) y ErrorValidacion publicable.
- src/tools/montos.py: cálculo de subtotal y total, invocado por validadores;
  la aritmética permanece en tools/, no en LLM ni en esquemas.
- docs/contratos/: 35 JSON Schema generados por scripts/exportar_esquemas.py.

## Reglas de entrada
ConsultaRequest requiere mensaje no vacío (hasta 4000 caracteres), canal web o
whatsapp y tenant_id explícito de formato limitado. No usa tenant por defecto.
Esto valida presencia y forma, no autenticación. El RAG filtra por tenant;
la seguridad previa al grafo está en src/core/seguridad.py.

Montos: céntimos PEN enteros no negativos; precios/totales positivos. Cantidades
enteras positivas. bool, números flotantes y cadenas numéricas no se convierten.
Selecciones entre 1 y 90 SKUs con formato mayúsculas y guiones. La existencia de
cada SKU se verifica con Catalogo, no con una expresión regular. Un kit RAM sigue
siendo una unidad de catálogo. Rango inclusivo, máximo opcional y mínimo por
defecto cero. No se impone techo arbitrario a consultas abiertas.

## Resultados y coherencia
Todos los modelos rechazan campos desconocidos. La validación posterior comprueba
subtotales/totales, fuentes por SKU, duplicados y coherencia entre flags y motivos.
ResultadoCotizacion comprueba que los bloqueos representen stock, presupuesto y
conflictos técnicos, y que los faltantes correspondan a sus líneas. No reconsulta
el catálogo: la autenticidad de precios, stock y evidencia depende de la herramienta
que produce el resultado. Un esquema válido no certifica un dato manipulado.

ResultadoTecnico distingue sin_conflictos_datos de aprobado_tecnicamente, siempre
false en esta demo. Las cotizaciones siempre requieren revisión y no generan
proforma. Los pagos solo admiten no_conciliado; pedidos solo borrador_demo.
ResultadoArmado puede no encontrar solución, sin inventar total ni mínimo real.

ConsultaResponse incluye version_contrato, naturaleza, status, intencion, mensaje,
hitl_requerido, motivos, fuentes, genera_proforma, aprobado_tecnicamente,
archivado_en_dlq y un resultado opcional acorde a su intención: cotizacion,
tecnico, stock, pago o pedido. Las otras ramas quedan null. Los
campos de aprobación son false, incluso cuando la consulta de stock está completada.
Los estados son completado, revision_humana, bloqueado y error. Un resultado que
exige revisión no puede declararse completado ni ocultar sus motivos/fuentes.
Bloqueado/error no admiten resultados de negocio; DLQ solo se puede declarar en
bloqueado. El campo por sí solo no acredita una escritura: la DLQ local se implementa en src/core/dlq.py.
El texto mensaje sirve para presentación; nunca determina el enrutamiento.
Los esquemas no ejecutan get_llm ni autorizan acciones: la decisión vive en src/core/.

## Privacidad y errores
Los mensajes y alias no aparecen en repr. hide_input_in_errors evita valores de
entrada en la representación textual de ValidationError; NO es un saneador de
model_dump(), JSON, errors(), json() del error, loc/context ni logs del llamador.
Nunca registrar solicitudes o excepciones crudas. ErrorValidacion tiene mensaje
fijo y lista limitada de nombres de campos declarados; rechaza claves arbitrarias
para impedir que una ruta de error incluya una identidad o SKU enviado por el usuario.
El adaptador público de errores está en src/api/main.py.
Modelos congelados impiden reasignación de atributos, pero no garantizan inmutabilidad
profunda de listas o diccionarios. Revalidar después de transformar datos; no usar
model_construct() ni model_copy(update=...) para aceptar entradas sin validación.

## Relación con los casos dorados
Los casos CP-1 a CP-7 se conservan; las pruebas de flujo/API verifican su implementación.
No se declara CP-1 aprobado; la demo exige evidencia de fabricante. CP-3 mantiene
el SKU agotado, CP-4 el límite, CP-5 no conciliado y CP-6 duplicado. Los campos de
esperado son aserciones semánticas, no todos campos literales de ConsultaResponse.
Presupuestos insuficientes de CP-7 no producen una configuración inventada.

## Uso y verificación
```python
from src.schemas.resultados import ResultadoCotizacion
from src.tools.catalogo import Catalogo
from src.tools.cotizacion import cotizar

# seleccion debe contener SKUs y cantidades existentes de demostración.
# resultado = ResultadoCotizacion.model_validate(cotizar(Catalogo(), seleccion))
# json_para_transporte = resultado.model_dump_json()
```

```powershell
.\.venv\Scripts\python -m pip install -r requirements-dev.txt
.\.venv\Scripts\Activate.ps1
python scripts/exportar_esquemas.py
python -m pytest tests/test_esquemas.py -q
python scripts/verificar.py
```

Los JSON Schema describen tipos y restricciones de campos. Las relaciones entre
campos se verifican con Pydantic; un consumidor que solo use JSON Schema debe
implementar esas comprobaciones. Dependencia: Pydantic 2.14.1; versiones fijadas en requirements.txt.
Referencia técnica: [modo estricto](https://docs.pydantic.dev/latest/concepts/strict_mode/)
y [validadores](https://docs.pydantic.dev/latest/concepts/validators/), documentación oficial.
