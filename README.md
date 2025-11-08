# Receipt Lens 🧾🔍

Sistema web auto-hospedado para analizar facturas de supermercado usando Claude AI. Sube fotos de tus tickets, extrae datos estructurados y obtén insights sobre tus hábitos de compra.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue.svg)](https://www.postgresql.org/)
[![Claude](https://img.shields.io/badge/Claude-Sonnet%204-orange.svg)](https://www.anthropic.com/)

## ✨ Features Principales

### 🤖 Análisis con IA
- **Múltiples Proveedores de Visión**: Soporta Claude, Google Vision, OCR.space y OpenAI
- **Configuración Flexible**: Elige el proveedor que mejor se adapte a tus necesidades
- **Opciones Gratuitas**: Google Vision (1,000/mes gratis) y OCR.space (500/día gratis)
- **Categorización Inteligente**: 8 categorías automáticas (bebidas, carne, verduras, lácteos, panadería, limpieza, ocio, otros)
- **Normalización de Productos**: Nombres de productos estandarizados
- **Validación de Datos**: Verificación de consistencia entre items y total

### 📊 Analytics Avanzados
- **Resúmenes Mensuales**: Gasto total, desglose por categoría, productos más comprados
- **Comparativa de Supermercados**: Índice de precios, mejores y peores ofertas
- **Evolución de Precios**: Seguimiento histórico de productos específicos
- **Detección de Tendencias**: Precios aumentando, disminuyendo o estables
- **Recomendaciones**: Ahorro potencial comprando en diferentes tiendas

### 🔒 Seguridad
- **Autenticación JWT**: Tokens con expiración de 24 horas
- **Bcrypt Hashing**: Contraseñas encriptadas con salt
- **Detección de Duplicados**: Hash SHA256 de imágenes
- **Validación de Inputs**: Pydantic schemas en todos los endpoints
- **User Ownership**: Verificación de propiedad en todas las queries

### 📈 Características Técnicas
- **API REST Completa**: 13 endpoints documentados con OpenAPI/Swagger
- **Paginación**: Listas de facturas con límites configurables
- **Formato Estandarizado**: Respuestas JSON consistentes
- **Manejo de Errores**: Logging detallado y mensajes user-friendly
- **Transacciones Seguras**: Rollback automático en errores

## 🛠️ Stack Tecnológico

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Base de Datos**: PostgreSQL 15 con SQLAlchemy 2.0
- **IA/Visión**: Múltiples proveedores (Claude, Google Vision, OCR.space, OpenAI)
- **Autenticación**: JWT (python-jose) + Bcrypt (passlib)
- **Validación**: Pydantic 2.5+
- **Testing**: pytest + httpx

### Infraestructura
- **Containerización**: Docker + Docker Compose
- **Almacenamiento**: Sistema de archivos local con estructura por usuario
- **Logging**: Python logging con niveles configurables

## 📁 Estructura del Proyecto

```
receipt-lens/
├── docker-compose.yml              # Orquestación Docker
├── Dockerfile                      # Imagen del backend
├── .env.example                   # Template de configuración
├── requirements.txt               # Dependencias Python
├── pytest.ini                     # Configuración de tests
├── backend/
│   ├── main.py                   # Aplicación FastAPI
│   ├── config.py                 # Settings con Pydantic
│   ├── dependencies.py           # Dependency injection
│   ├── auth/                     # Módulo de autenticación
│   │   ├── models.py            # User model
│   │   ├── schemas.py           # Pydantic schemas
│   │   ├── service.py           # Lógica de negocio
│   │   └── router.py            # Endpoints (/api/auth/*)
│   ├── receipts/                # Módulo de facturas
│   │   ├── models.py            # Receipt, Item, Category models
│   │   ├── schemas.py           # Pydantic schemas
│   │   ├── claude_analyzer.py   # Integración Claude AI
│   │   ├── service.py           # Lógica de negocio
│   │   └── router.py            # Endpoints (/api/receipts/*)
│   ├── analytics/               # Módulo de analytics
│   │   ├── schemas.py           # Pydantic schemas
│   │   ├── service.py           # Cálculos y agregaciones
│   │   └── router.py            # Endpoints (/api/analytics/*)
│   └── database/
│       ├── base.py              # SQLAlchemy Base
│       ├── session.py           # Engine y SessionLocal
│       └── init.sql             # Schema PostgreSQL
├── frontend/                     # Frontend web application
│   ├── static/
│   │   ├── css/
│   │   │   ├── main.css          # Estilos principales
│   │   │   └── dashboard.css     # Estilos del dashboard
│   │   └── js/
│   │       ├── api.js            # Cliente API
│   │       └── utils.js          # Funciones utilitarias
│   ├── index.html                # Página de inicio
│   ├── login.html                # Login/Registro
│   ├── dashboard.html            # Dashboard principal
│   ├── upload.html               # Subida de facturas
│   ├── receipts.html             # Lista de facturas
│   ├── receipt-detail.html       # Detalle de factura
│   ├── analytics.html            # Analytics y gráficos
│   └── profile.html              # Perfil de usuario
├── tests/
│   ├── conftest.py              # Fixtures de pytest
│   ├── test_auth.py             # Tests de autenticación (28 tests)
│   └── test_receipts.py         # Tests de receipts (pendiente)
├── scripts/
│   └── init_db.py               # Script de inicialización DB
└── uploads/                      # Almacenamiento de imágenes
    └── user_{id}/               # Carpeta por usuario
```

## 🚀 Quick Start

### Prerrequisitos

- **Docker** 20.10+
- **Docker Compose** 2.0+
- **API Key de Visión** (ver [VISION_PROVIDERS.md](VISION_PROVIDERS.md) para opciones gratuitas y de pago)

### Instalación

1. **Clonar el repositorio**
   ```bash
   git clone https://github.com/amalonso/receipt-lens.git
   cd receipt-lens
   ```

2. **Configurar variables de entorno**
   ```bash
   cp .env.example .env
   ```

3. **Editar .env con tus credenciales**
   ```bash
   # REQUERIDO: Contraseña segura para PostgreSQL
   POSTGRES_PASSWORD=tu_contraseña_segura

   # REQUERIDO: Secret key para JWT (generar con: openssl rand -hex 32)
   JWT_SECRET_KEY=tu_secret_key_generada

   # Proveedor de Visión (ver VISION_PROVIDERS.md para más opciones)
   VISION_PROVIDER=ocrspace  # o claude, google_vision, openai

   # API Keys (solo configurar para el proveedor que uses)
   OCRSPACE_API_KEY=helloworld  # Gratis - 500 requests/día
   # ANTHROPIC_API_KEY=sk-ant-...  # Claude (de pago)
   # GOOGLE_VISION_CREDENTIALS=/path/to/credentials.json  # 1,000/mes gratis
   # OPENAI_API_KEY=sk-...  # OpenAI (de pago)
   ```

   **📋 Guía de Proveedores:**
   - **Para empezar gratis**: Usa `VISION_PROVIDER=ocrspace` (500/día gratis)
   - **Para mejor precisión**: Usa `VISION_PROVIDER=claude` (requiere API key de pago)
   - **Para uso personal**: Usa `VISION_PROVIDER=google_vision` (1,000/mes gratis)
   - Ver [VISION_PROVIDERS.md](VISION_PROVIDERS.md) para comparación completa

4. **Iniciar servicios con Docker**
   ```bash
   docker-compose up -d
   ```

5. **Verificar que todo funciona**
   ```bash
   # Health check
   curl http://localhost:8000/api/health

   # Documentación API
   open http://localhost:8000/api/docs
   ```

### Primera Configuración

**Opción 1: Script de inicialización (recomendado)**
```bash
docker-compose exec backend python scripts/init_db.py
```
Esto te guiará interactivamente para crear un usuario admin.

**Opción 2: Usar la API directamente**
```bash
# Registrar usuario
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "email": "admin@example.com",
    "password": "AdminPass123"
  }'
```

## 🖥️ Uso del Frontend

Una vez iniciado el sistema con Docker, accede a la aplicación web en:

**http://localhost:8000**

### Flujo de Uso

1. **Registro/Login**
   - Crea una cuenta nueva o inicia sesión con tus credenciales
   - Las contraseñas deben tener al menos 8 caracteres, incluir mayúsculas y números
   - El sistema te redirigirá automáticamente al dashboard

2. **Dashboard Principal**
   - Vista general de tus gastos del mes
   - Estadísticas de facturas, productos y tiendas visitadas
   - Gráfico de gastos por categoría (bebidas, carne, verduras, etc.)
   - Lista de productos más comprados
   - Acceso rápido a facturas recientes

3. **Subir Facturas**
   - Arrastra y suelta tu factura o haz clic para seleccionar
   - Formatos soportados: JPG, PNG, PDF (máx. 10MB)
   - Claude AI analiza automáticamente la imagen
   - Extracción de tienda, fecha, productos, precios y categorías
   - Vista previa del resultado con detalles completos

4. **Mis Facturas**
   - Lista completa de todas tus facturas
   - Búsqueda por nombre de tienda
   - Ordenamiento por fecha o monto
   - Eliminación de facturas con confirmación
   - Clic en cualquier factura para ver detalle completo

5. **Analytics**
   - **Resumen del período**: Estadísticas generales por mes
   - **Comparación de supermercados**: Índice de precios, mejores y peores ofertas por tienda
   - **Evolución de precios**: Busca cualquier producto y ve su historial de precios con gráficos interactivos
   - Tendencias de precios (aumentando, disminuyendo, estables)
   - Recomendaciones de ahorro

6. **Perfil**
   - Información de tu cuenta
   - Estadísticas personales
   - Información del sistema

### Características del Frontend

- **Diseño Moderno**: Interfaz limpia y profesional con paleta de colores coherente
- **Responsive**: Funciona perfectamente en desktop, tablet y móvil
- **Sidebar Navigation**: Navegación intuitiva con iconos y destacado de sección activa
- **Visualizaciones**: Gráficos interactivos con Chart.js para análisis visual
- **Drag & Drop**: Subida de archivos mediante arrastre para mejor UX
- **Validación en Tiempo Real**: Feedback inmediato en formularios
- **Notificaciones Toast**: Alertas elegantes para acciones del usuario
- **Carga Asíncrona**: Spinners y estados de carga para mejor feedback
- **Modal Dialogs**: Confirmaciones elegantes para acciones destructivas

## 📖 Uso de la API

El sistema también expone una API REST completa que puedes usar programáticamente.

### Autenticación

```bash
# 1. Registrar usuario
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "usuario",
    "email": "usuario@example.com",
    "password": "Password123"
  }'

# 2. Login (obtener token)
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "usuario",
    "password": "Password123"
  }'

# Respuesta:
# {
#   "success": true,
#   "data": {
#     "user": { "id": 1, "username": "usuario", ... },
#     "token": {
#       "access_token": "eyJ0eXAiOiJKV1QiLCJh...",
#       "token_type": "bearer",
#       "expires_in": 86400
#     }
#   }
# }

# 3. Obtener usuario actual
curl http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer <tu_token>"
```

### Subir y Analizar Facturas

```bash
# Subir factura (máx 10MB, formatos: jpg, png, pdf)
curl -X POST http://localhost:8000/api/receipts/upload \
  -H "Authorization: Bearer <tu_token>" \
  -F "file=@/ruta/a/factura.jpg"

# Respuesta:
# {
#   "success": true,
#   "data": {
#     "receipt": {
#       "id": 1,
#       "store_name": "Mercadona",
#       "purchase_date": "2025-11-08",
#       "total_amount": 45.67,
#       "processed": true,
#       ...
#     },
#     "message": "Receipt uploaded and analyzed successfully. 12 items extracted."
#   }
# }

# Listar facturas (paginado)
curl "http://localhost:8000/api/receipts?page=1&page_size=20" \
  -H "Authorization: Bearer <tu_token>"

# Ver detalle de factura con items
curl http://localhost:8000/api/receipts/1 \
  -H "Authorization: Bearer <tu_token>"

# Eliminar factura
curl -X DELETE http://localhost:8000/api/receipts/1 \
  -H "Authorization: Bearer <tu_token>"
```

### Analytics

```bash
# Resumen mensual
curl "http://localhost:8000/api/analytics/monthly-summary?month=11&year=2025" \
  -H "Authorization: Bearer <tu_token>"

# Respuesta incluye:
# - Total gastado, número de facturas y items
# - Desglose por categoría con porcentajes
# - Top 10 productos más comprados
# - Promedio por factura
# - Lista de tiendas visitadas

# Comparar supermercados (últimos 6 meses)
curl "http://localhost:8000/api/analytics/store-comparison?months=6" \
  -H "Authorization: Bearer <tu_token>"

# Respuesta incluye por cada tienda:
# - Índice de precios (100 = promedio, >100 = más caro, <100 = más barato)
# - Mejores ofertas (productos más baratos que el promedio)
# - Peores ofertas (productos más caros que el promedio)
# - Total gastado y visitas

# Evolución de precios de un producto
curl "http://localhost:8000/api/analytics/price-evolution?product=leche&months=6" \
  -H "Authorization: Bearer <tu_token>"

# Respuesta incluye:
# - Historial de precios por tienda
# - Precio mín, máx y promedio por tienda
# - Tendencia (increasing/decreasing/stable)
# - Mejor y peor tienda para ese producto
```

## 🗄️ Modelo de Datos

### Tablas Principales

```sql
-- Usuarios
users (id, username, email, password_hash, created_at)

-- Categorías (8 predefinidas)
categories (id, name)
  - bebidas, carne, verduras, lácteos
  - panadería, limpieza, ocio, otros

-- Facturas
receipts (
  id, user_id, store_name, purchase_date,
  total_amount, image_path, image_hash,
  processed, created_at
)

-- Items de facturas
items (
  id, receipt_id, category_id, product_name,
  quantity, unit_price, total_price, created_at
)
```

### Índices Optimizados

- `idx_receipts_user_date` - Búsquedas por usuario y fecha
- `idx_receipts_store` - Filtrado por tienda
- `idx_receipts_image_hash` - Detección de duplicados
- `idx_items_receipt` - JOIN receipt-items
- `idx_items_category` - Agregaciones por categoría
- `idx_items_product` - Búsqueda de productos

## 🧪 Testing

### Ejecutar Tests

```bash
# Todos los tests
docker-compose exec backend pytest

# Solo tests de autenticación
docker-compose exec backend pytest tests/test_auth.py -v

# Con coverage
docker-compose exec backend pytest --cov=backend --cov-report=html

# Ver reporte de coverage
open htmlcov/index.html
```

### Estado Actual de Tests

- **Autenticación**: 24/28 tests passing (85.7%)
  - ✅ Registro exitoso
  - ✅ Login con username y email
  - ✅ JWT tokens válidos/inválidos
  - ✅ Detección de duplicados
  - ✅ Validación de passwords
  - ✅ Hashing seguro (bcrypt)
  - ⚠️ 4 tests con warnings de Pydantic v1/v2 syntax

## 📊 API Reference

### Endpoints Disponibles

#### Health & Info
- `GET /` - Información de la API
- `GET /api/health` - Health check
- `GET /api/docs` - Swagger UI (solo desarrollo)
- `GET /api/redoc` - ReDoc (solo desarrollo)

#### Authentication (`/api/auth`)
- `POST /register` - Registrar usuario
- `POST /login` - Login y obtener JWT
- `GET /me` - Obtener usuario actual

#### Receipts (`/api/receipts`)
- `POST /upload` - Subir y analizar factura
- `GET /` - Listar facturas (paginado)
- `GET /{id}` - Detalle de factura
- `DELETE /{id}` - Eliminar factura

#### Analytics (`/api/analytics`)
- `GET /monthly-summary` - Resumen mensual
- `GET /store-comparison` - Comparar tiendas
- `GET /price-evolution` - Evolución de precios

### Formato de Respuesta Estándar

```json
{
  "success": true,
  "data": { ... },
  "error": null
}
```

En caso de error:
```json
{
  "success": false,
  "data": null,
  "error": "Mensaje de error descriptivo"
}
```

## 🔧 Configuración Avanzada

### Variables de Entorno

```bash
# Base de datos
DATABASE_URL=postgresql://user:pass@host:port/db
POSTGRES_DB=receipt_lens
POSTGRES_USER=admin
POSTGRES_PASSWORD=contraseña_segura

# Proveedor de Visión
VISION_PROVIDER=claude|google_vision|ocrspace|openai

# API Keys (configurar solo el proveedor que uses)
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_VISION_CREDENTIALS=/path/to/credentials.json
OCRSPACE_API_KEY=helloworld
OPENAI_API_KEY=sk-...

# Seguridad
JWT_SECRET_KEY=secret_key_generada
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Aplicación
ENVIRONMENT=development|production
DEBUG=true|false
LOG_LEVEL=DEBUG|INFO|WARNING|ERROR

# Upload
MAX_UPLOAD_SIZE_MB=10
UPLOAD_DIR=/app/uploads
ALLOWED_EXTENSIONS=jpg,jpeg,png,pdf
UPLOAD_RATE_LIMIT_PER_HOUR=10

# CORS
CORS_ORIGINS=http://localhost:8000,http://localhost:3000
```

### Docker Compose Personalizado

Para producción, crea `docker-compose.override.yml`:

```yaml
version: '3.8'

services:
  backend:
    restart: always
    environment:
      - ENVIRONMENT=production
      - DEBUG=false

  db:
    volumes:
      - ./backups:/backups
```

## 📈 Roadmap

### ✅ Fase 1 - MVP (Completado)
- [x] Setup Docker + PostgreSQL
- [x] Autenticación completa con JWT
- [x] Upload de imágenes + Claude AI
- [x] Almacenamiento transaccional
- [x] Tests de autenticación

### ✅ Fase 2 - Analytics (Completado)
- [x] Resúmenes mensuales
- [x] Comparativas de supermercados
- [x] Evolución de precios
- [x] Detección de tendencias

### ✅ Fase 3 - Frontend (Completado)
- [x] Login/Register UI con validación
- [x] Upload con drag & drop
- [x] Dashboard con Chart.js
- [x] Lista y detalle de facturas
- [x] Visualizaciones de analytics
- [x] Diseño responsive y moderno
- [x] Navegación con sidebar
- [x] Página de perfil de usuario

### 📅 Futuras Mejoras
- [ ] Tests de receipts y analytics
- [ ] Rate limiting implementation
- [ ] Background jobs para Claude (Celery)
- [ ] Cache de analytics (Redis)
- [ ] Export a PDF/CSV
- [ ] Email notifications
- [ ] Budget goals y alerts
- [ ] Mobile app (React Native)
- [ ] Shared receipts entre usuarios
- [ ] Predicción de gastos (ML)

## 🐛 Troubleshooting

### La base de datos no inicia

```bash
# Verificar logs
docker-compose logs db

# Reiniciar servicio
docker-compose restart db

# Recrear volumen (⚠️ elimina datos)
docker-compose down -v
docker-compose up -d
```

### Vision API devuelve errores

- Verificar que `VISION_PROVIDER` esté configurado correctamente
- Verificar API key correspondiente en `.env`
- Para Claude: verificar quota en https://console.anthropic.com/
- Para Google Vision: verificar credenciales y proyecto
- Para OCR.space: verificar límites de rate (500/día gratis)
- Revisar logs: `docker-compose logs backend | grep vision`
- Ver [VISION_PROVIDERS.md](VISION_PROVIDERS.md) para troubleshooting específico

### Upload de archivos falla

- Verificar tamaño < 10MB
- Formatos soportados: jpg, jpeg, png, pdf
- Verificar permisos del directorio `uploads/`
- Revisar logs: `docker-compose logs backend | grep upload`

### Tests fallan

```bash
# Limpiar cache de pytest
docker-compose exec backend pytest --cache-clear

# Reinstalar dependencias
docker-compose exec backend pip install -r requirements.txt --force-reinstall

# Verificar variables de entorno
docker-compose exec backend python -c "from backend.config import settings; print(settings.dict())"
```

## 🤝 Contribuir

Las contribuciones son bienvenidas! Por favor:

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/amazing-feature`)
3. Commit tus cambios (`git commit -m 'Add amazing feature'`)
4. Push a la rama (`git push origin feature/amazing-feature`)
5. Abre un Pull Request

### Guías de Contribución

- Seguir PEP 8 para Python
- Añadir tests para nuevas features
- Actualizar documentación
- Usar type hints
- Mantener coverage > 70%

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para detalles.

## 🙏 Agradecimientos

- [Anthropic](https://www.anthropic.com/) por Claude AI
- [FastAPI](https://fastapi.tiangolo.com/) por el framework
- [PostgreSQL](https://www.postgresql.org/) por la base de datos
- [SQLAlchemy](https://www.sqlalchemy.org/) por el ORM

## 📧 Contacto

- **Autor**: amalonso
- **Repositorio**: [github.com/amalonso/receipt-lens](https://github.com/amalonso/receipt-lens)
- **Issues**: [github.com/amalonso/receipt-lens/issues](https://github.com/amalonso/receipt-lens/issues)

---

**Receipt Lens** - Análisis inteligente de facturas con IA 🧾🔍
