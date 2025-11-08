# Receipt Lens - API Examples

Ejemplos completos de uso de la API Receipt Lens con curl.

## 📋 Tabla de Contenidos

- [Configuración Inicial](#configuración-inicial)
- [Autenticación](#autenticación)
- [Gestión de Facturas](#gestión-de-facturas)
- [Analytics](#analytics)
- [Casos de Uso Completos](#casos-de-uso-completos)

---

## Configuración Inicial

```bash
# Variables de entorno (sustituir con valores reales)
export API_URL="http://localhost:8000"
export TOKEN=""  # Se obtendrá después del login
```

---

## Autenticación

### 1. Registrar Usuario Nuevo

```bash
curl -X POST "${API_URL}/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "juan",
    "email": "juan@example.com",
    "password": "JuanPass123"
  }'
```

**Respuesta esperada:**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": 1,
      "username": "juan",
      "email": "juan@example.com",
      "created_at": "2025-11-08T10:30:00"
    },
    "token": {
      "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
      "token_type": "bearer",
      "expires_in": 86400
    }
  },
  "error": null
}
```

### 2. Login (Obtener Token)

```bash
# Login con username
curl -X POST "${API_URL}/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "juan",
    "password": "JuanPass123"
  }'

# O login con email
curl -X POST "${API_URL}/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "juan@example.com",
    "password": "JuanPass123"
  }'
```

**Guardar el token:**
```bash
# Extraer y guardar el token
export TOKEN=$(curl -s -X POST "${API_URL}/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"juan","password":"JuanPass123"}' | \
  jq -r '.data.token.access_token')

echo "Token guardado: ${TOKEN:0:20}..."
```

### 3. Obtener Usuario Actual

```bash
curl "${API_URL}/api/auth/me" \
  -H "Authorization: Bearer ${TOKEN}"
```

---

## Gestión de Facturas

### 1. Subir y Analizar una Factura

```bash
# Subir factura desde archivo local
curl -X POST "${API_URL}/api/receipts/upload" \
  -H "Authorization: Bearer ${TOKEN}" \
  -F "file=@./factura_mercadona.jpg"

# Subir factura PDF
curl -X POST "${API_URL}/api/receipts/upload" \
  -H "Authorization: Bearer ${TOKEN}" \
  -F "file=@./ticket_carrefour.pdf"
```

**Respuesta esperada:**
```json
{
  "success": true,
  "data": {
    "receipt": {
      "id": 1,
      "store_name": "Mercadona",
      "purchase_date": "2025-11-08",
      "total_amount": 45.67,
      "image_path": "/app/uploads/user_1/20251108_120000_abc12345.jpg",
      "processed": true,
      "created_at": "2025-11-08T12:00:00"
    },
    "message": "Receipt uploaded and analyzed successfully. 12 items extracted."
  },
  "error": null
}
```

### 2. Listar Facturas (Paginado)

```bash
# Primera página (20 facturas)
curl "${API_URL}/api/receipts?page=1&page_size=20" \
  -H "Authorization: Bearer ${TOKEN}"

# Segunda página
curl "${API_URL}/api/receipts?page=2&page_size=20" \
  -H "Authorization: Bearer ${TOKEN}"

# Página personalizada (50 facturas por página)
curl "${API_URL}/api/receipts?page=1&page_size=50" \
  -H "Authorization: Bearer ${TOKEN}"
```

**Respuesta esperada:**
```json
{
  "success": true,
  "data": {
    "receipts": [
      {
        "id": 5,
        "store_name": "Mercadona",
        "purchase_date": "2025-11-08",
        "total_amount": 45.67,
        "processed": true,
        "item_count": 12,
        "created_at": "2025-11-08T12:00:00"
      },
      // ... más facturas
    ],
    "total": 45,
    "page": 1,
    "page_size": 20,
    "total_pages": 3
  },
  "error": null
}
```

### 3. Ver Detalle de una Factura

```bash
# Ver factura con todos sus items
curl "${API_URL}/api/receipts/1" \
  -H "Authorization: Bearer ${TOKEN}"
```

**Respuesta esperada:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "user_id": 1,
    "store_name": "Mercadona",
    "purchase_date": "2025-11-08",
    "total_amount": 45.67,
    "image_path": "/app/uploads/user_1/20251108_120000_abc12345.jpg",
    "processed": true,
    "created_at": "2025-11-08T12:00:00",
    "items": [
      {
        "product_name": "Leche Entera",
        "category": "lácteos",
        "quantity": 2.0,
        "unit_price": 0.89,
        "total_price": 1.78
      },
      {
        "product_name": "Pan de Molde",
        "category": "panadería",
        "quantity": 1.0,
        "unit_price": null,
        "total_price": 1.25
      },
      // ... más items
    ]
  },
  "error": null
}
```

### 4. Eliminar una Factura

```bash
# Eliminar factura por ID
curl -X DELETE "${API_URL}/api/receipts/1" \
  -H "Authorization: Bearer ${TOKEN}"
```

**Respuesta esperada:**
```json
{
  "success": true,
  "data": {
    "message": "Receipt 1 deleted successfully"
  },
  "error": null
}
```

---

## Analytics

### 1. Resumen Mensual

```bash
# Resumen del mes actual
MONTH=$(date +%-m)
YEAR=$(date +%Y)

curl "${API_URL}/api/analytics/monthly-summary?month=${MONTH}&year=${YEAR}" \
  -H "Authorization: Bearer ${TOKEN}"

# Resumen de un mes específico (ej: Octubre 2025)
curl "${API_URL}/api/analytics/monthly-summary?month=10&year=2025" \
  -H "Authorization: Bearer ${TOKEN}"
```

**Respuesta esperada:**
```json
{
  "success": true,
  "data": {
    "month": 11,
    "year": 2025,
    "total_spent": 234.56,
    "receipts_count": 8,
    "items_count": 89,
    "avg_receipt_amount": 29.32,
    "stores_visited": ["Mercadona", "Carrefour", "Lidl"],
    "spending_by_category": [
      {
        "category": "verduras",
        "amount": 45.30,
        "percentage": 19.31,
        "item_count": 15
      },
      {
        "category": "carne",
        "amount": 42.15,
        "percentage": 17.97,
        "item_count": 8
      },
      {
        "category": "lácteos",
        "amount": 38.20,
        "percentage": 16.29,
        "item_count": 12
      },
      // ... más categorías
    ],
    "top_products": [
      {
        "product_name": "Leche Entera",
        "times_purchased": 6,
        "total_spent": 10.68,
        "avg_price": 1.78,
        "stores": ["Mercadona", "Carrefour"]
      },
      // ... más productos
    ]
  },
  "error": null
}
```

### 2. Comparar Supermercados

```bash
# Comparar últimos 6 meses (default)
curl "${API_URL}/api/analytics/store-comparison" \
  -H "Authorization: Bearer ${TOKEN}"

# Comparar últimos 3 meses
curl "${API_URL}/api/analytics/store-comparison?months=3" \
  -H "Authorization: Bearer ${TOKEN}"

# Comparar último año
curl "${API_URL}/api/analytics/store-comparison?months=12" \
  -H "Authorization: Bearer ${TOKEN}"
```

**Respuesta esperada:**
```json
{
  "success": true,
  "data": {
    "stores": [
      {
        "store_name": "Lidl",
        "total_spent": 345.60,
        "visit_count": 12,
        "avg_receipt_amount": 28.80,
        "items_count": 156,
        "price_index": 92.5,
        "best_deals": [
          {
            "product": "Leche Entera",
            "price": 0.79,
            "avg_price": 0.92,
            "difference": -0.13,
            "percentage_diff": -14.13
          },
          // ... más ofertas
        ],
        "worst_deals": [
          {
            "product": "Pan Integral",
            "price": 1.85,
            "avg_price": 1.45,
            "difference": 0.40,
            "percentage_diff": 27.59
          },
          // ... más productos caros
        ]
      },
      {
        "store_name": "Mercadona",
        "price_index": 100.0,
        // ... datos de Mercadona
      },
      {
        "store_name": "Carrefour",
        "price_index": 107.3,
        // ... datos de Carrefour
      }
    ],
    "total_stores": 3,
    "overall_avg_price": 3.45
  },
  "error": null
}
```

**Interpretación del Price Index:**
- `< 100`: Más barato que el promedio
- `= 100`: Precio promedio
- `> 100`: Más caro que el promedio

### 3. Evolución de Precios de un Producto

```bash
# Seguir precio de leche últimos 6 meses
curl "${API_URL}/api/analytics/price-evolution?product=leche&months=6" \
  -H "Authorization: Bearer ${TOKEN}"

# Seguir precio de pan últimos 3 meses
curl "${API_URL}/api/analytics/price-evolution?product=pan&months=3" \
  -H "Authorization: Bearer ${TOKEN}"

# Producto específico con nombre exacto
curl "${API_URL}/api/analytics/price-evolution?product=Leche%20Entera&months=12" \
  -H "Authorization: Bearer ${TOKEN}"
```

**Respuesta esperada:**
```json
{
  "success": true,
  "data": {
    "product_name": "leche",
    "months": 6,
    "by_store": [
      {
        "store_name": "Lidl",
        "avg_price": 0.82,
        "min_price": 0.79,
        "max_price": 0.89,
        "price_trend": "stable",
        "prices": [
          {
            "date": "2025-09-15",
            "price": 0.79,
            "store": "Lidl",
            "receipt_id": 3
          },
          {
            "date": "2025-10-02",
            "price": 0.82,
            "store": "Lidl",
            "receipt_id": 8
          },
          // ... más puntos de precio
        ]
      },
      {
        "store_name": "Mercadona",
        "avg_price": 0.89,
        "min_price": 0.85,
        "max_price": 0.92,
        "price_trend": "increasing",
        "prices": [
          // ... historial de precios
        ]
      }
    ],
    "overall_avg_price": 0.86,
    "best_store": "Lidl",
    "worst_store": "Carrefour",
    "total_purchases": 18
  },
  "error": null
}
```

**Tipos de Price Trend:**
- `"increasing"`: Precio subiendo >5%
- `"decreasing"`: Precio bajando >5%
- `"stable"`: Variación <5%

---

## Casos de Uso Completos

### Caso 1: Nuevo Usuario con Primera Factura

```bash
#!/bin/bash

# 1. Registrar usuario
echo "Registrando usuario..."
RESPONSE=$(curl -s -X POST "${API_URL}/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "maria",
    "email": "maria@example.com",
    "password": "MariaPass123"
  }')

# 2. Extraer token
TOKEN=$(echo $RESPONSE | jq -r '.data.token.access_token')
echo "Token obtenido: ${TOKEN:0:20}..."

# 3. Subir primera factura
echo "Subiendo factura..."
curl -X POST "${API_URL}/api/receipts/upload" \
  -H "Authorization: Bearer ${TOKEN}" \
  -F "file=@./mi_factura.jpg"

# 4. Ver resumen del mes actual
echo "Obteniendo resumen mensual..."
curl "${API_URL}/api/analytics/monthly-summary?month=$(date +%-m)&year=$(date +%Y)" \
  -H "Authorization: Bearer ${TOKEN}" | jq '.'
```

### Caso 2: Análisis Mensual Completo

```bash
#!/bin/bash

# Obtener resumen del mes actual
MONTH=$(date +%-m)
YEAR=$(date +%Y)

echo "📊 Resumen de compras ${MONTH}/${YEAR}"
echo "========================================="

# 1. Resumen general
SUMMARY=$(curl -s "${API_URL}/api/analytics/monthly-summary?month=${MONTH}&year=${YEAR}" \
  -H "Authorization: Bearer ${TOKEN}")

echo "Total gastado: €$(echo $SUMMARY | jq -r '.data.total_spent')"
echo "Número de facturas: $(echo $SUMMARY | jq -r '.data.receipts_count')"
echo "Promedio por factura: €$(echo $SUMMARY | jq -r '.data.avg_receipt_amount')"

# 2. Top 3 categorías
echo ""
echo "Top 3 categorías de gasto:"
echo $SUMMARY | jq -r '.data.spending_by_category[:3][] | "  - \(.category): €\(.amount) (\(.percentage)%)"'

# 3. Top 5 productos
echo ""
echo "Top 5 productos más comprados:"
echo $SUMMARY | jq -r '.data.top_products[:5][] | "  - \(.product_name): \(.times_purchased) veces, €\(.total_spent)"'
```

### Caso 3: Comparar Precios de un Producto

```bash
#!/bin/bash

PRODUCT="leche"

echo "🔍 Análisis de precios: ${PRODUCT}"
echo "========================================="

# 1. Obtener evolución de precios
EVOLUTION=$(curl -s "${API_URL}/api/analytics/price-evolution?product=${PRODUCT}&months=6" \
  -H "Authorization: Bearer ${TOKEN}")

# 2. Mostrar mejor y peor tienda
echo "Mejor tienda: $(echo $EVOLUTION | jq -r '.data.best_store')"
echo "Peor tienda: $(echo $EVOLUTION | jq -r '.data.worst_store')"
echo "Precio promedio general: €$(echo $EVOLUTION | jq -r '.data.overall_avg_price')"

# 3. Detalles por tienda
echo ""
echo "Precios por tienda:"
echo $EVOLUTION | jq -r '.data.by_store[] | "  \(.store_name): €\(.avg_price) (tendencia: \(.price_trend))"'
```

### Caso 4: Encontrar Mejores Ofertas

```bash
#!/bin/bash

echo "💰 Mejores ofertas por supermercado"
echo "========================================="

# Obtener comparación de supermercados
COMPARISON=$(curl -s "${API_URL}/api/analytics/store-comparison?months=6" \
  -H "Authorization: Bearer ${TOKEN}")

# Mostrar ofertas de cada tienda
echo $COMPARISON | jq -r '.data.stores[] |
  "
\(.store_name) (Índice de precio: \(.price_index))
Mejores ofertas:
\(.best_deals[:3][] | "  - \(.product): €\(.price) (ahorro: €\(-(.difference)))")
"'
```

### Caso 5: Subir Múltiples Facturas

```bash
#!/bin/bash

# Subir todas las facturas de un directorio
for FILE in ./facturas/*.{jpg,png,pdf}; do
  if [ -f "$FILE" ]; then
    echo "Subiendo: $FILE"
    curl -s -X POST "${API_URL}/api/receipts/upload" \
      -H "Authorization: Bearer ${TOKEN}" \
      -F "file=@${FILE}" | jq '.data.message'

    # Esperar 2 segundos entre uploads
    sleep 2
  fi
done

echo "✅ Todas las facturas han sido procesadas"
```

---

## Scripts de Utilidad

### Generar Token de Prueba

```bash
# Guardar en ~/.receipt-lens-token
curl -s -X POST "${API_URL}/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "tu_usuario",
    "password": "tu_password"
  }' | jq -r '.data.token.access_token' > ~/.receipt-lens-token

# Usar el token guardado
export TOKEN=$(cat ~/.receipt-lens-token)
```

### Health Check

```bash
# Verificar que el servicio está activo
curl -s "${API_URL}/api/health" | jq '.'
```

### Listar Todas las Facturas

```bash
# Obtener todas las facturas (paginadas)
PAGE=1
while true; do
  RESPONSE=$(curl -s "${API_URL}/api/receipts?page=${PAGE}&page_size=50" \
    -H "Authorization: Bearer ${TOKEN}")

  # Mostrar facturas
  echo $RESPONSE | jq -r '.data.receipts[] | "\(.id): \(.store_name) - €\(.total_amount)"'

  # Verificar si hay más páginas
  TOTAL_PAGES=$(echo $RESPONSE | jq -r '.data.total_pages')
  if [ $PAGE -ge $TOTAL_PAGES ]; then
    break
  fi

  PAGE=$((PAGE + 1))
done
```

---

## Manejo de Errores

### Error 401: No Autenticado

```json
{
  "detail": "Could not validate credentials"
}
```

**Solución**: Verificar que el token es válido y está en el header.

### Error 400: Datos Inválidos

```json
{
  "success": false,
  "data": null,
  "error": "Validation error",
  "details": [...]
}
```

**Solución**: Revisar los datos enviados según la documentación.

### Error 409: Factura Duplicada

```json
{
  "detail": "This receipt has already been uploaded (Receipt ID: 5)"
}
```

**Solución**: Esta factura ya existe en el sistema.

### Error 413: Archivo Demasiado Grande

```json
{
  "detail": "File too large. Maximum size: 10MB"
}
```

**Solución**: Reducir el tamaño del archivo o comprimirlo.

---

## Recursos Adicionales

- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc
- **Health Check**: http://localhost:8000/api/health

---

**Receipt Lens** - Ejemplos de uso de la API 🧾🔍
