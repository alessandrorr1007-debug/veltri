# Contrato de datos v1.0

Todos los registros son sintéticos, con fecha de referencia 2026-10-17. No hay
consulta de mercado ni mediciones físicas. Identificadores estables y únicos,
mayúsculas y guiones. Ausencia de evidencia requiere revisión, nunca aprobación.

## Metadatos comunes a los JSON
version_esquema: versión del contrato; naturaleza: demostracion_sintetica;
moneda: PEN (soles); fecha_referencia: fecha ISO, no fecha de actualización de
inventario real; aviso: limitación de uso. No contienen datos personales.

## catalogo.json
productos: lista de 84 objetos. sku: identificador; nombre: etiqueta de demo,
no modelo comercial completo; categoria: cpu, placa, gpu, ram, ssd, fuente,
gabinete o refrigeracion; precio_centimos: entero positivo (100 = S/ 1.00),
sin floats; stock: unidades enteras no negativas, sin reservas implementadas;
especificaciones: campos según categoría. No confundir precio con centavos de USD.

CPU: socket y potencia_diseno_w (cota ilustrativa, no TDP oficial).
Placa: socket, chipset, ram_tipo, formato, ranuras_ram, ram_max_gb,
interfaces_ssd y bios_requiere_verificacion.
GPU: potencia_diseno_w, longitud_mm, conectores_requeridos (tipo → cantidad).
RAM: ram_tipo, capacidad_total_gb del kit, modulos y velocidad_mt_s.
SSD: capacidad_gb, interfaz, generacion_pcie y formato físico 2280.
Fuente: potencia_nominal_w, formato y conectores disponibles (tipo → cantidad).
Gabinete: formatos_placa, formatos_fuente, gpu_max_mm, cooler_max_mm.
Refrigeración: sockets, altura_mm, capacidad_diseno_w (supuesto sintético).
Unidades: W, mm, GB y MT/s explícitas en los nombres. Solo refrigeración por aire.
Los conectores de GPU son un ejercicio simplificado; no describen necesariamente
las tarjetas comerciales que comparten nombre. Confirmar modelo exacto en producción.

## compatibilidad.json
sockets: mapa de plataformas a chipsets y tipos RAM admisibles; LGA1700 puede
usar DDR4 o DDR5 según placa, nunca ambas por defecto.
relaciones_cpu_placa: pares de SKUs existentes, estado requiere_verificacion y
motivo; cubren todos los pares de igual socket, sin certificar soporte de BIOS.
ram, refrigeracion y montaje: restricciones declarativas; su validación se implementó en FASE 2.
SSD requiere interfaz M2-NVME-PCIE; generación no implica velocidad garantizada.
potencia: reserva de 100 W y margen de 25% propuestos, fórmula con redondeo hacia
arriba y verificación de conectores; no garantiza transitorios ni calidad de fuente.
La fórmula supone una CPU y una GPU; sin GPU dedicada su término sería cero,
pero no se presupone que toda CPU tenga gráficos integrados.
evidencia: fabricante_verificado=false, faltantes a revisión y ausencia de
porcentajes de cuello de botella. Ninguna relación representa una medición real.

## Verificación y alcance
python scripts/verificar.py ejecuta ruff, pytest y escaneo de secretos.
Las pruebas de datos comprueban rango de SKUs, valores, categorías, referencias,
plataformas, campos técnicos y el agotado CP-3. CP-1 a CP-7 siguen siendo escenarios
futuros, no pruebas funcionales integradas del sistema. Las herramientas de FASE 2
se documentan en docs/herramientas.md; aún no hay agentes.
