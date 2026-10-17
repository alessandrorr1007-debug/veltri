# API FastAPI — FASE 8

Punto de entrada HTTP de Veltri Tecnologic que expone el orquestador multiagente
mediante el endpoint `POST /consulta`. Garantiza el cumplimiento estricto del invariante 7:
toda respuesta pública es un JSON estructurado con el contrato `ConsultaResponse`.

## Características y diseño

1. **Endpoint único (`POST /consulta`)**:
   - Recibe `SolicitudAPI` ([flujo.py](file:///d:/Proyectos/veltri-orquestador/src/schemas/flujo.py)),
     admitiendo formato plano (`mensaje`, `canal`, `tenant_id` y `parametros` opcionales)
     o anidado con objeto `consulta`.
   - Transforma la petición a `SolicitudFlujo` y la pasa al `Orquestador`.
   - Devuelve `ConsultaResponse 1.0-demo` con los datos tipados de la respuesta.

2. **Sin dependencias CDN (regla permanente)**:
   - `docs_url=None` y `redoc_url=None` en la instancia de FastAPI para evitar
     cargas externas desde `cdn.jsdelivr.net`.
   - Cumple la directiva de autonomía local y cero peticiones externas no autorizadas.

3. **Manejo uniforme de errores (Invariantes 5 y 7)**:
   - `RequestValidationError` (422): Errores de sintaxis JSON o tipos inválidos devuelven
     un `ConsultaResponse` con `status="error"`, `intencion="desconocida"`,
     `hitl_requerido=false` y `motivos=["entrada_invalida"]`.
   - `StarletteHTTPException` (404/otros): Rutas inexistentes devuelven un `ConsultaResponse`
     con `status="error"` y `motivos=["ruta_no_encontrada"]`.
   - `Exception` general (500): Fallos no previstos se capturan dentro del endpoint devolviendo
     `ConsultaResponse` con `status="error"` y `motivos=["fallo_interno"]`, impidiendo
     la fuga de trazas o excepciones en texto crudo.

4. **Integración con seguridad y DLQ (CP-2)**:
   - Todo mensaje pasa primero por `validar_entrada_modelo` antes de entrar al grafo.
   - Peticiones con inyección de prompt o datos personales (DNI, correo, teléfono)
     devuelven `status="bloqueado"`, `archivado_en_dlq=true`, `genera_proforma=false`
     y registran un evento técnico anónimo en la DLQ en memoria.

## Comandos y ejecución

- **Servidor local para desarrollo**:
  ```powershell
  .\.venv\Scripts\uvicorn src.api.main:app --reload --port 8000
  ```
- **Pruebas de la API**:
  ```powershell
  .\.venv\Scripts\python -m pytest tests/test_api.py -v
  ```
- **Verificación completa**:
  ```powershell
  .\.venv\Scripts\python scripts/verificar.py
  ```

## Ejemplo de petición y respuesta

```http
POST /consulta HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{
  "mensaje": "Hola, deseo cotizar una PC gamer con presupuesto de S/ 3500",
  "canal": "web",
  "tenant_id": "veltri",
  "parametros": {
    "tipo": "armar",
    "solicitud": {
      "maximo_centimos": 350000
    }
  }
}
```

Respuesta (200 OK):
```json
{
  "version_contrato": "1.0-demo",
  "naturaleza": "demostracion_sintetica",
  "status": "revision_humana",
  "intencion": "cotizacion",
  "mensaje": "Resultado de demostración; consulta fuentes y evidencia antes de operar.",
  "hitl_requerido": true,
  "motivos": [
    "verificar_soporte_cpu_bios"
  ],
  "fuentes": [
    "data/catalogo.json",
    "data/compatibilidad.json"
  ],
  "genera_proforma": false,
  "aprobado_tecnicamente": false,
  "archivado_en_dlq": false,
  "cotizacion": { ... }
}
```
