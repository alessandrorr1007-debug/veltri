# Fase 4.3 — lanzador de un solo uso

`scripts/langsmith_segundo_intento.py` ejecuta la misma demo fija de stock con MockLLM.
No modifica agentes, política ni contratos comerciales. Requiere permiso humano
expreso de envío y confirmación de revocación/reemplazo de la clave expuesta.

El registro fijo `docs/evidencias/semana10-fase43/ejecucion-unica.json` se crea con
modo exclusivo antes de la demo. Si existe, el lanzador no vuelve a ejecutar. No
eliminarlo para repetir la prueba; una autorización nueva requiere otro procedimiento.
Las pruebas usan registros temporales distintos y transporte HTTP simulado.

Se validan proyecto, endpoint US, presencia de clave sin mostrarla, flags iniciales
apagados y modelos MockLLM antes de cada plan. Ambos opt-in se activan solo en el
proceso. `.env` no se modifica. Cada cuerpo del SDK se valida por lista permitida
antes del adaptador; inputs/outputs vacíos, metadata fija, UUID/tiempos/padres y orden
coherentes. Se admite una raíz, nueve altas y un cierre por alta.

El transporte seguro conserva el primer fallo, bloquea destinos alternativos,
redirects y reintentos. Un error aborta el procedimiento incluso si el SDK o la
fachada comercial intentan manejarlo. No se guarda cuerpo crudo ni excepción original.
Los registros HTTP conservan solo campos cerrados de Fase 4.2.

Solo después de completar las nueve altas y nueve cierres, se apaga escritura y
se permiten hasta diez lecturas: nueve runs y su proyecto. No se repiten lecturas.
Se cotejan ID, trace_id, padre, dotted_order, nombre, duración, inputs/outputs y
metadata. Si hay diferencia o error, se detiene sin más consultas. HTTP 202 por sí
solo no acredita persistencia. El run_id se marca verificado únicamente después
de cotejar todo el árbol y el nombre del proyecto remoto.

El bloque finally apaga los flags globales y ambos opt-in, cierra transportes y
conserva el resultado seguro. El registro de autorización se mantiene consumido
aunque haya error o interrupción. Tras finalizar hay que verificar también los
flags persistentes de `.env`, sin mostrar su contenido.

## Comando reservado a la autorización de Fase 4.3

```powershell
.venv/Scripts/python scripts/langsmith_segundo_intento.py --enviar-autorizado --rotacion-confirmada
```

No ejecutar como prueba local: consume el registro único y puede conectar con el
servicio si ambos permisos humanos ya fueron concedidos. La validación previa es
`python scripts/verificar.py`, con SDK y transporte simulados en los tests.

## Capturas posteriores, solo si existe traza verificada

- Proyecto veltri-semana10-demo con la raíz consulta visible y rango horario correcto.
- Detalle del run_id, duración y estado técnico del run.
- Árbol de spans: consulta, seguridad, A1.plan_mock, validar_plan, dominio,
  A5.plan_mock, comprobar_stock, decidir y responder; padre de A5/herramienta es dominio.
- Inputs/outputs vacíos y metadata synthetic=true/model_mode=mock/scenario=stock_demo.
- Resultado comercial local separado: requiere HITL, sin aprobación real ni pago.

No mostrar configuración de claves, headers o proyectos ajenos. No eludir el bloqueo
de Computer Use. El usuario puede obtener las capturas manualmente del panel.

## Límites

No garantiza resolver el HTTP 400 histórico. Las solicitudes aceptadas pueden no estar
disponibles inmediatamente para lectura; se espera una sola vez y se consulta sin
polling ni reintentos. Una lectura fallida no autoriza repetir la demo.
