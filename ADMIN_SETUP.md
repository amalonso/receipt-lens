# Configuración de la Interfaz de Administración

Este documento explica cómo configurar y usar la nueva interfaz de administración de Receipt Lens.

## Características de la Interfaz de Administración

La interfaz de administración incluye las siguientes funcionalidades:

### 1. **Dashboard de Administración** (`/admin-dashboard.html`)
- Métricas del sistema (usuarios, facturas, gastos, costes API)
- Gráficos de crecimiento de usuarios y costes de API
- Análisis de uso detallado por usuario y período
- Log de actividad reciente del sistema

### 2. **Gestión de Usuarios** (`/admin-users.html`)
- Lista completa de usuarios con estadísticas
- Búsqueda y filtrado por nombre, email, estado y rol
- Activar/desactivar cuentas de usuario
- Promover usuarios a administrador o quitar privilegios
- Ver detalles completos de cada usuario

### 3. **Analytics Global** (`/admin-analytics.html`)
- Dashboard de compras agregado de todos los usuarios
- Ver analytics de un usuario específico
- Gráficos de gasto mensual y por categoría
- Top tiendas y productos más comprados

### 4. **Configuración del Sistema** (`/admin-settings.html`)
- Ver y editar configuración del sistema en tiempo real
- Configuración de proveedor de visión/AI
- Parámetros de subida de archivos
- Configuración de seguridad
- Log de cambios de configuración con auditoría

### 5. **Características Adicionales**
- **Auditoría completa**: Registro de todas las acciones administrativas
- **Tracking de costes API**: Seguimiento de costes por usuario y período
- **Control de acceso**: Solo usuarios con rol de administrador pueden acceder
- **Sistema de roles**: Nuevos campos `is_admin` e `is_active` en usuarios

## Instalación y Configuración

### Paso 1: Aplicar la Migración de Base de Datos

La migración agrega las siguientes tablas y campos:

**Nuevos campos en `users`:**
- `is_admin` (BOOLEAN): Indica si el usuario es administrador
- `is_active` (BOOLEAN): Indica si la cuenta está activa
- `last_login` (TIMESTAMP): Última fecha de login
- `updated_at` (TIMESTAMP): Última actualización

**Nuevas tablas:**
- `api_costs`: Tracking de costes de llamadas a APIs de visión
- `activity_logs`: Log de auditoría de acciones del sistema
- `system_config`: Configuración del sistema editable

**Nuevas vistas:**
- `admin_user_stats`: Estadísticas de usuarios
- `admin_daily_metrics`: Métricas diarias del sistema
- `admin_monthly_usage`: Uso mensual por usuario
- Y más vistas para analytics...

### Opción A: Usar el Script de Setup (Recomendado)

```bash
# Dentro del contenedor Docker
docker-compose exec backend python scripts/setup_admin.py
```

Este script:
1. Ejecuta la migración de base de datos
2. Hace al primer usuario registrado un administrador
3. Muestra una lista de todos los usuarios

**Comandos adicionales:**

```bash
# Hacer admin a un usuario específico
docker-compose exec backend python scripts/setup_admin.py --make-admin USERNAME

# Listar todos los usuarios
docker-compose exec backend python scripts/setup_admin.py --list

# Ver ayuda
docker-compose exec backend python scripts/setup_admin.py --help
```

### Opción B: Ejecutar la Migración Manualmente

```bash
# Dentro del contenedor Docker o con acceso a PostgreSQL
psql -U receipt_lens_user -d receipt_lens -f backend/database/migrations/001_add_admin_features.sql
```

Luego, hacer admin al primer usuario:

```sql
UPDATE users SET is_admin = true, is_active = true WHERE id = 1;
```

## Uso de la Interfaz de Administración

### 1. Acceder al Panel de Admin

Una vez que tu usuario tiene permisos de administrador:

1. Inicia sesión normalmente
2. Verás una nueva sección "Administración" en el menú lateral
3. Haz clic en "Panel de Admin" para acceder al dashboard

### 2. Gestión de Usuarios

Desde `/admin-users.html` puedes:

- **Buscar usuarios**: Usa la barra de búsqueda para filtrar por nombre o email
- **Filtrar por estado**: Ver solo usuarios activos o inactivos
- **Filtrar por rol**: Ver solo administradores o usuarios normales
- **Activar/Desactivar**: Haz clic en el icono 🔒/🔓 para cambiar el estado
  - ⚠️ No puedes desactivar tu propia cuenta
- **Promover/Degradar**: Haz clic en el icono 👑/👤 para cambiar el rol
- **Ver detalles**: Haz clic en 👁️ para ver estadísticas detalladas del usuario

### 3. Ver Analytics Global

Desde `/admin-analytics.html`:

- Por defecto muestra datos agregados de todos los usuarios
- Usa el selector para ver analytics de un usuario específico
- Visualiza gráficos de gasto mensual y por categoría
- Revisa las top tiendas y productos más comprados

### 4. Configurar el Sistema

Desde `/admin-settings.html`:

1. Busca la configuración que deseas modificar
2. Haz clic en "✏️ Editar"
3. Introduce el nuevo valor
4. Haz clic en "Guardar"

⚠️ **Importante**: Los cambios se aplican inmediatamente y pueden afectar el funcionamiento del sistema.

**Configuraciones disponibles:**

- `vision_provider`: Proveedor de AI (claude, google_vision, openai, etc.)
- `max_upload_size_mb`: Tamaño máximo de subida en MB
- `upload_rate_limit_per_hour`: Límite de subidas por hora por usuario
- `jwt_expiration_hours`: Tiempo de expiración de tokens JWT
- `enable_registration`: Permitir/deshabilitar registro de nuevos usuarios
- `enable_duplicate_detection`: Detectar facturas duplicadas
- Y más...

### 5. Monitoring y Auditoría

El sistema registra automáticamente:

- **Cambios en usuarios**: Activación/desactivación, cambios de rol
- **Cambios en configuración**: Todos los cambios con valores antiguos y nuevos
- **Login de usuarios**: Fecha y hora del último login
- **Costes de API**: Cada llamada a la API de visión con su coste

Puedes ver estos logs en:
- Dashboard principal: Actividad reciente (últimas 20 acciones)
- Configuración: Log de cambios de configuración

## Endpoints de API

La interfaz de administración consume los siguientes endpoints:

### Usuarios
- `GET /api/admin/users` - Listar usuarios con filtros
- `PATCH /api/admin/users/{id}/toggle-active` - Activar/desactivar usuario
- `PATCH /api/admin/users/{id}/toggle-admin` - Cambiar rol de usuario
- `GET /api/admin/users/{id}/statistics` - Estadísticas de usuario

### Dashboard y Analytics
- `GET /api/admin/dashboard` - Métricas del sistema
- `GET /api/admin/usage-analytics` - Análisis de uso con costes
- `GET /api/admin/analytics/user/{id}` - Analytics de usuario específico
- `GET /api/admin/analytics/aggregated` - Analytics agregado

### Configuración
- `GET /api/admin/config` - Obtener toda la configuración
- `GET /api/admin/config/{key}` - Obtener configuración específica
- `PATCH /api/admin/config/{key}` - Actualizar configuración

### Logs y Actividad
- `GET /api/admin/activity-logs` - Logs de actividad con filtros
- `GET /api/admin/receipts` - Ver todas las facturas (cross-user)

Todos estos endpoints requieren autenticación con rol de administrador.

## Seguridad

### Control de Acceso

- Todos los endpoints de admin requieren el header `Authorization: Bearer <token>`
- El token debe pertenecer a un usuario con `is_admin = true` y `is_active = true`
- Si un usuario no es admin, recibirá un error 403 Forbidden

### Protección en Frontend

Las páginas de admin verifican automáticamente:
1. Si el usuario está autenticado
2. Si el usuario tiene rol de administrador
3. Redirige a login o dashboard según corresponda

### Auditoría

Todas las acciones administrativas se registran en la tabla `activity_logs` con:
- Usuario que ejecutó la acción
- Tipo de acción
- Entidad afectada
- Detalles adicionales en formato JSON
- Timestamp

## Tracking de Costes de API

Para habilitar el tracking de costes, necesitas modificar el servicio de receipts para registrar los costes después de cada llamada a la API de visión.

Ejemplo de cómo registrar un coste:

```python
from backend.admin.models import ApiCost

# Después de procesar una factura con la API
api_cost = ApiCost(
    user_id=user_id,
    receipt_id=receipt_id,
    provider="claude",  # o el proveedor que uses
    model="claude-3-opus",
    input_tokens=1500,
    output_tokens=500,
    cost_usd=0.045,  # Calcular según el pricing del proveedor
    processing_time_ms=2500,
    success=True
)
db.add(api_cost)
db.commit()
```

## Solución de Problemas

### No puedo acceder al panel de admin

1. Verifica que tu usuario tenga `is_admin = true`:
   ```sql
   SELECT id, username, is_admin, is_active FROM users WHERE username = 'tu_usuario';
   ```

2. Si no eres admin, ejecuta:
   ```sql
   UPDATE users SET is_admin = true WHERE username = 'tu_usuario';
   ```

### La migración falla

1. Verifica que la base de datos esté corriendo:
   ```bash
   docker-compose ps
   ```

2. Verifica la conexión:
   ```bash
   docker-compose exec db psql -U receipt_lens_user -d receipt_lens -c "\dt"
   ```

3. Si ya ejecutaste la migración parcialmente, puede que necesites hacer rollback manual.

### Los cambios de configuración no se aplican

Los cambios en `system_config` se reflejan inmediatamente en la tabla, pero la aplicación backend puede estar usando variables de entorno en lugar de la base de datos.

Para que la configuración de la base de datos tenga prioridad, necesitarás modificar `backend/config.py` para leer de la tabla `system_config` primero.

## Próximas Mejoras

Posibles mejoras futuras para la interfaz de administración:

- [ ] Gráficos de tiempo real con WebSockets
- [ ] Exportar reportes en PDF/Excel
- [ ] Notificaciones por email para eventos críticos
- [ ] Sistema de backups automatizado
- [ ] Dashboard de métricas de rendimiento
- [ ] Gestión de categorías personalizada
- [ ] Bulk operations para usuarios
- [ ] Rate limiting por usuario
- [ ] Alertas de costes de API

## Soporte

Si encuentras algún problema o tienes sugerencias, por favor crea un issue en el repositorio de GitHub.
