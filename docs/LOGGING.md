# Sistema de Logging de Receipt Lens

Este documento explica cómo funciona el sistema de logging y cómo configurarlo según tus necesidades.

## Configuración

El sistema de logging se configura mediante variables de entorno en el archivo `.env`:

### Variables de Logging Principal

```bash
# Nivel de logging de la aplicación
LOG_LEVEL=DEBUG
```

**Niveles disponibles:**
- `DEBUG`: Muestra todos los mensajes incluyendo detalles del análisis de imágenes
- `INFO`: Muestra mensajes informativos sobre el flujo de la aplicación
- `WARNING`: Solo muestra advertencias y errores
- `ERROR`: Solo muestra errores
- `CRITICAL`: Solo muestra errores críticos

### Variables de Logging de Base de Datos

```bash
# Activar/desactivar el logging de queries SQL de SQLAlchemy
DB_ECHO=false

# Nivel de logging de SQLAlchemy
DB_LOG_LEVEL=WARNING
```

**DB_ECHO:**
- `true`: SQLAlchemy mostrará TODAS las queries SQL ejecutadas
- `false`: SQLAlchemy no mostrará las queries SQL (recomendado)

**DB_LOG_LEVEL:**
- Controla el nivel de los mensajes internos de SQLAlchemy
- Valores: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
- Recomendado: `WARNING` para no saturar los logs

## Ejemplos de Configuración

### Desarrollo - Ver todo el detalle del análisis de imágenes

```bash
LOG_LEVEL=DEBUG
DB_ECHO=false
DB_LOG_LEVEL=WARNING
```

Esta configuración te permite:
- ✅ Ver todos los detalles del análisis de las imágenes subidas
- ✅ Ver el proceso de extracción de datos
- ✅ Ver los items detectados en cada recibo
- ❌ No ver las queries SQL de la base de datos (que no son relevantes)

### Desarrollo - Ver también las queries SQL

```bash
LOG_LEVEL=DEBUG
DB_ECHO=true
DB_LOG_LEVEL=DEBUG
```

Esta configuración te permite:
- ✅ Ver todos los detalles del análisis de las imágenes
- ✅ Ver todas las queries SQL ejecutadas
- ✅ Debuggear problemas de base de datos

### Producción - Solo errores y advertencias

```bash
LOG_LEVEL=WARNING
DB_ECHO=false
DB_LOG_LEVEL=ERROR
```

Esta configuración:
- ✅ Minimiza el ruido en los logs
- ✅ Solo muestra problemas importantes
- ✅ Mejora el rendimiento al reducir I/O de logs

## Qué verás en cada nivel

### Con LOG_LEVEL=DEBUG

```
2024-01-09 10:30:15 - backend.receipts.service - INFO - Starting analysis with provider: google_vision...
2024-01-09 10:30:15 - backend.receipts.service - DEBUG - Image saved at: /app/uploads/user_1/20240109_103015_abc12345.jpg
2024-01-09 10:30:15 - backend.receipts.service - DEBUG - File size: 245678 bytes
2024-01-09 10:30:15 - backend.receipts.service - DEBUG - File hash: abc123def456...
2024-01-09 10:30:15 - backend.receipts.service - DEBUG - Analyzer created: GoogleVisionAnalyzer
2024-01-09 10:30:15 - backend.receipts.service - DEBUG - ============================================================
2024-01-09 10:30:15 - backend.receipts.service - DEBUG - Starting receipt image analysis...
2024-01-09 10:30:15 - backend.receipts.service - DEBUG - ============================================================
2024-01-09 10:30:16 - backend.receipts.google_vision_analyzer - INFO - Starting receipt analysis with Google Vision: /app/uploads/user_1/20240109_103015_abc12345.jpg
2024-01-09 10:30:16 - backend.receipts.google_vision_analyzer - INFO - Sending request to Google Cloud Vision API...
2024-01-09 10:30:17 - backend.receipts.google_vision_analyzer - INFO - Google Vision extracted 450 characters of text
2024-01-09 10:30:17 - backend.receipts.google_vision_analyzer - DEBUG - Extracted text preview: MERCADONA\nC/ PRINCIPAL 123...
2024-01-09 10:30:17 - backend.receipts.google_vision_analyzer - DEBUG - Parsing receipt text with 15 lines
2024-01-09 10:30:17 - backend.receipts.google_vision_analyzer - DEBUG - Extracted store name: MERCADONA
2024-01-09 10:30:17 - backend.receipts.google_vision_analyzer - DEBUG - Found total amount 25.50 from line: TOTAL 25.50
2024-01-09 10:30:17 - backend.receipts.service - DEBUG - ============================================================
2024-01-09 10:30:17 - backend.receipts.service - DEBUG - Analysis completed, validating results...
2024-01-09 10:30:17 - backend.receipts.service - DEBUG - Store name: MERCADONA
2024-01-09 10:30:17 - backend.receipts.service - DEBUG - Purchase date: 2024-01-09
2024-01-09 10:30:17 - backend.receipts.service - DEBUG - Total amount: 25.5
2024-01-09 10:30:17 - backend.receipts.service - DEBUG - Number of items: 5
2024-01-09 10:30:17 - backend.receipts.service - DEBUG -   Item 1: Pan integral - panadería - Qty: 2.0 - Price: 1.80
2024-01-09 10:30:17 - backend.receipts.service - DEBUG -   Item 2: Leche desnatada - lácteos - Qty: 1.0 - Price: 0.95
2024-01-09 10:30:17 - backend.receipts.service - DEBUG -   Item 3: Tomates - frutas_verduras - Qty: 0.5 - Price: 2.50
2024-01-09 10:30:17 - backend.receipts.service - DEBUG -   Item 4: Arroz integral - despensa - Qty: 1.0 - Price: 1.20
2024-01-09 10:30:17 - backend.receipts.service - DEBUG -   Item 5: Aceite oliva - despensa - Qty: 1.0 - Price: 19.05
2024-01-09 10:30:17 - backend.receipts.service - DEBUG - ============================================================
2024-01-09 10:30:17 - backend.receipts.vision_analyzer - INFO - Analysis validation passed
2024-01-09 10:30:17 - backend.receipts.service - INFO - Analysis validation successful: 5 items extracted
```

### Con LOG_LEVEL=INFO

```
2024-01-09 10:30:15 - backend.receipts.service - INFO - Starting analysis with provider: google_vision...
2024-01-09 10:30:16 - backend.receipts.google_vision_analyzer - INFO - Starting receipt analysis with Google Vision: /app/uploads/user_1/20240109_103015_abc12345.jpg
2024-01-09 10:30:16 - backend.receipts.google_vision_analyzer - INFO - Sending request to Google Cloud Vision API...
2024-01-09 10:30:17 - backend.receipts.google_vision_analyzer - INFO - Google Vision extracted 450 characters of text
2024-01-09 10:30:17 - backend.receipts.vision_analyzer - INFO - Analysis validation passed
2024-01-09 10:30:17 - backend.receipts.service - INFO - Analysis validation successful: 5 items extracted
```

## Solución de Problemas

### No veo mensajes de DEBUG

**Problema:** Aunque tengo `DEBUG=true` en `.env`, no veo mensajes de debug.

**Solución:** Asegúrate de tener `LOG_LEVEL=DEBUG` en tu archivo `.env`. La variable `DEBUG` controla otras funcionalidades pero no el nivel de logging directamente.

### Veo demasiados mensajes de SQLAlchemy

**Problema:** Los logs están llenos de queries SQL y mensajes de SQLAlchemy.

**Solución:** Configura en tu `.env`:
```bash
DB_ECHO=false
DB_LOG_LEVEL=WARNING
```

### Quiero ver las queries SQL pero no otros mensajes de SQLAlchemy

**Problema:** Necesito debuggear queries pero los logs de conexiones saturan.

**Solución:** Configura en tu `.env`:
```bash
DB_ECHO=true
DB_LOG_LEVEL=WARNING
```

El `DB_ECHO=true` mostrará las queries SQL, pero `DB_LOG_LEVEL=WARNING` ocultará los mensajes internos de SQLAlchemy.

## Mejores Prácticas

1. **Desarrollo local:** Usa `LOG_LEVEL=DEBUG` y `DB_ECHO=false`
2. **Debugging de DB:** Usa `LOG_LEVEL=DEBUG` y `DB_ECHO=true` temporalmente
3. **Producción:** Usa `LOG_LEVEL=INFO` o `WARNING` y `DB_ECHO=false`
4. **Performance:** Niveles más altos de logging (WARNING, ERROR) mejoran el rendimiento

## Estructura de los Loggers

La aplicación usa diferentes loggers para cada componente:

- `backend.main` - Aplicación principal y configuración
- `backend.receipts.service` - Lógica de negocio de recibos
- `backend.receipts.vision_analyzer` - Análisis base de imágenes
- `backend.receipts.google_vision_analyzer` - Google Cloud Vision
- `backend.receipts.claude_analyzer` - Claude AI
- `backend.receipts.openai_vision_analyzer` - OpenAI GPT-4 Vision
- `backend.receipts.paddleocr_analyzer` - PaddleOCR local
- `sqlalchemy.engine` - Queries SQL y transacciones
- `sqlalchemy.pool` - Pool de conexiones
- `sqlalchemy.orm` - Operaciones ORM

Cada logger respeta la configuración global pero SQLAlchemy se puede controlar independientemente.
