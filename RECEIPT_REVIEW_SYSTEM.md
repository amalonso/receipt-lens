# Sistema de Revisión de Facturas

Este documento describe el sistema de revisión de facturas implementado en Receipt Lens.

## Descripción General

El sistema de revisión permite a los administradores revisar el proceso de análisis de facturas y solucionar problemas reportados por los usuarios. Guarda temporalmente los datos necesarios para la revisión y los elimina automáticamente después de un período configurable.

## Características Principales

### 1. Guardado Automático de Datos de Revisión

Cuando un usuario sube una factura, el sistema automáticamente guarda:
- **Imagen original de la factura**
- **Sistema de análisis utilizado** (Claude, OpenAI, Google Vision, etc.)
- **Respuesta completa del análisis** (JSON)

Estos datos se almacenan en la tabla `receipt_review_data` y están vinculados a la factura final.

### 2. Reporte de Mal Funcionamiento por Usuarios

Los usuarios pueden reportar problemas con el análisis de una factura:

**Endpoint:** `POST /api/receipts/{receipt_id}/report`

```json
{
  "message": "Opcional: descripción del problema"
}
```

**Respuesta:**
```json
{
  "success": true,
  "data": {
    "message": "Gracias por tu feedback. Tu reporte será revisado por un administrador."
  },
  "error": null
}
```

### 3. Panel de Administración

Los administradores tienen acceso a varios endpoints para revisar facturas:

#### 3.1 Listar Facturas para Revisión

**Endpoint:** `GET /api/admin/receipt-reviews`

**Parámetros:**
- `page`: Número de página (default: 1)
- `page_size`: Registros por página (default: 20, max: 100)
- `reported_only`: Filtrar solo reportadas (true/false)
- `analyzer_used`: Filtrar por analizador (claude, openai, google_vision, etc.)

**Ejemplo:**
```bash
# Ver todas las facturas reportadas
GET /api/admin/receipt-reviews?reported_only=true

# Ver solo facturas analizadas con Claude
GET /api/admin/receipt-reviews?analyzer_used=claude
```

#### 3.2 Ver Detalles de una Revisión

**Endpoint:** `GET /api/admin/receipt-reviews/{review_id}`

Retorna todos los detalles incluyendo:
- Imagen de la factura
- Analizador utilizado
- Respuesta completa del análisis (JSON)
- Estado de reporte
- Mensaje del usuario (si fue reportada)

#### 3.3 Probar Otros Analizadores

**Endpoint:** `POST /api/admin/receipt-reviews/{review_id}/test-analyzer`

Permite al administrador probar la misma imagen con diferentes analizadores para comparar resultados.

**Body:**
```json
{
  "analyzer_name": "openai"
}
```

**Respuesta:**
```json
{
  "success": true,
  "analyzer_name": "openai",
  "analysis_response": "{...}",
  "error": null,
  "processing_time_ms": 2341
}
```

**Analizadores disponibles:**
- `claude` - Claude Sonnet 4.5 (Anthropic)
- `openai` - GPT-4 Vision (OpenAI)
- `google_vision` - Google Cloud Vision API
- `ocrspace` - OCR.space API
- `grok` - Grok Vision (xAI)

#### 3.4 Marcar como Revisada

**Endpoint:** `PATCH /api/admin/receipt-reviews/{review_id}/mark-reviewed`

Marca la revisión como completada y guarda la fecha/hora de revisión.

### 4. Limpieza Automática de Datos

El sistema incluye un proceso programado que elimina automáticamente los datos de revisión antiguos.

#### Configuración de Retención

La retención de datos se configura mediante el parámetro `review_data_retention_days` en la tabla `system_config`.

**Obtener configuración actual:**
```bash
GET /api/admin/config/review_data_retention_days
```

**Actualizar configuración:**
```bash
PATCH /api/admin/config/review_data_retention_days
{
  "config_value": "45"  # Retener durante 45 días
}
```

**Valor por defecto:** 30 días

#### Programación de Limpieza

- **Frecuencia:** Diariamente a las 3:00 AM
- **Acción:** Elimina registros de `receipt_review_data` más antiguos que el período de retención
- **IMPORTANTE:** Solo elimina datos de revisión, NUNCA los datos de factura

#### Limpieza Manual

Los administradores pueden ejecutar la limpieza manualmente:

**Endpoint:** `POST /api/admin/maintenance/cleanup-review-data`

**Respuesta:**
```json
{
  "success": true,
  "data": {
    "success": true,
    "deleted_count": 125,
    "retention_days": 30
  },
  "message": "Cleanup completed: 125 records deleted"
}
```

## Instalación y Migración

### Para Instalaciones Nuevas

1. Instalar dependencias:
```bash
pip install -r requirements.txt
```

2. Inicializar base de datos:
```bash
python scripts/init_db.py
```

Esto creará todas las tablas incluyendo `receipt_review_data` y configurará los valores por defecto.

### Para Instalaciones Existentes

1. Instalar nuevas dependencias:
```bash
pip install apscheduler==3.10.4
```

2. Ejecutar script de migración:
```bash
python scripts/migrate_add_review_data.py
```

Esto agregará:
- Tabla `receipt_review_data`
- Configuración `review_data_retention_days` (30 días por defecto)

3. Reiniciar la aplicación para activar el scheduler

## Estructura de Datos

### Tabla: receipt_review_data

```sql
CREATE TABLE receipt_review_data (
    id SERIAL PRIMARY KEY,
    receipt_id INTEGER NOT NULL REFERENCES receipts(id) ON DELETE CASCADE,
    image_path VARCHAR(255) NOT NULL,
    analyzer_used VARCHAR(50) NOT NULL,
    analysis_response TEXT NOT NULL,  -- JSON string
    reported BOOLEAN DEFAULT FALSE NOT NULL,
    report_message TEXT,
    reviewed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Índices
CREATE INDEX idx_receipt_review_data_reported ON receipt_review_data(reported);
CREATE INDEX idx_receipt_review_data_analyzer ON receipt_review_data(analyzer_used);
CREATE INDEX idx_receipt_review_data_created_at ON receipt_review_data(created_at);
```

## Flujo de Trabajo Típico

### Para Usuarios

1. Usuario sube factura → Sistema analiza y guarda datos de revisión automáticamente
2. Usuario revisa resultado
3. Si hay problemas → Usuario hace clic en "Reportar problema"
4. Usuario recibe confirmación de que será revisado

### Para Administradores

1. Administrador accede a `/api/admin/receipt-reviews?reported_only=true`
2. Ve lista de facturas reportadas
3. Selecciona una factura para revisar
4. Ve la imagen original, el análisis y los datos del reporte
5. Puede probar diferentes analizadores para comparar resultados
6. Identifica y documenta el problema
7. Marca como revisada

### Limpieza Automática

1. Cada día a las 3:00 AM
2. Sistema calcula fecha límite (hoy - retention_days)
3. Elimina todos los registros de review_data más antiguos
4. Registra en logs la cantidad de registros eliminados

## Logs

El sistema registra eventos importantes:

```
INFO - Saved review data for receipt 123 using analyzer: claude
INFO - Receipt 123 marked as reported by user 45
INFO - Receipt review 456 marked as reviewed
INFO - Starting scheduled cleanup of old review data...
INFO - Cleanup completed: Deleted 125 review data records (older than 30 days)
```

## Seguridad

- ✅ Todos los endpoints de admin requieren autenticación y privilegios de administrador
- ✅ Los usuarios solo pueden reportar sus propias facturas
- ✅ Las imágenes están protegidas por el sistema de archivos del servidor
- ✅ La limpieza automática solo elimina datos de revisión, nunca datos de factura

## Configuración Recomendada

| Entorno | Retención Recomendada |
|---------|----------------------|
| Desarrollo | 7 días |
| Testing | 14 días |
| Producción | 30-90 días |

## Troubleshooting

### El scheduler no inicia

**Problema:** Error al iniciar el scheduler en logs

**Solución:**
```bash
# Verificar que APScheduler está instalado
pip install apscheduler==3.10.4

# Reiniciar la aplicación
docker-compose restart backend
```

### No se guardan datos de revisión

**Problema:** Las facturas nuevas no tienen datos de revisión

**Solución:**
```bash
# Verificar que la tabla existe
python scripts/migrate_add_review_data.py

# Revisar logs de la aplicación
docker-compose logs backend | grep "review data"
```

### Limpieza no funciona

**Problema:** Los datos antiguos no se eliminan

**Solución:**
```bash
# Ejecutar limpieza manual
curl -X POST http://localhost:8000/api/admin/maintenance/cleanup-review-data \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"

# Verificar configuración de retención
curl http://localhost:8000/api/admin/config/review_data_retention_days \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

## Preguntas Frecuentes

### ¿Se guardan las imágenes duplicadas?

No, el sistema usa la misma imagen que ya está guardada para la factura. No se duplican archivos.

### ¿Qué pasa si elimino una factura?

Cuando se elimina una factura (`DELETE /api/receipts/{id}`), la relación CASCADE elimina automáticamente sus datos de revisión asociados.

### ¿Puedo cambiar la hora de la limpieza automática?

Sí, edita `backend/scheduler.py` y modifica el `CronTrigger`:

```python
scheduler.add_job(
    cleanup_old_review_data,
    trigger=CronTrigger(hour=2, minute=30),  # 2:30 AM
    ...
)
```

### ¿Los datos de revisión afectan las analytics?

No, las analytics se calculan solo con los datos de la tabla `receipts` y `items`. Los datos de revisión son independientes.

## Soporte

Para problemas o preguntas sobre el sistema de revisión:
1. Revisar los logs de la aplicación
2. Ejecutar el script de migración si es una instalación existente
3. Verificar la configuración de retención en el panel de admin
