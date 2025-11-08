# Vision API Providers

Receipt Lens soporta múltiples proveedores de APIs de visión para el análisis de imágenes de recibos. Puedes elegir el proveedor que mejor se adapte a tus necesidades en términos de costo, precisión y disponibilidad.

## Proveedores Disponibles

### 1. Claude (Anthropic) ⭐ Recomendado

**Descripción:** Utiliza Claude Sonnet 4 de Anthropic para análisis avanzado de imágenes con comprensión contextual.

**Ventajas:**
- Análisis más preciso y contextual
- Excelente comprensión de texto en español
- Extracción estructurada de datos
- Categorización inteligente de productos

**Desventajas:**
- Requiere API key de pago
- No tiene tier gratuito real

**Configuración:**
```env
VISION_PROVIDER=claude
ANTHROPIC_API_KEY=sk-ant-xxxxx
```

**Precio:**
- Entrada: ~$3 por millón de tokens
- Salida: ~$15 por millón de tokens
- Aprox. $0.01-0.05 por recibo procesado

**Obtener API Key:** [Anthropic Console](https://console.anthropic.com/)

---

### 2. Google Cloud Vision API

**Descripción:** API de Google Cloud para OCR y detección de texto en imágenes.

**Ventajas:**
- ✅ **1,000 imágenes/mes GRATIS**
- OCR robusto y confiable
- Buen soporte multiidioma
- Infraestructura escalable de Google

**Desventajas:**
- Requiere parsing adicional del texto extraído
- Menos preciso en categorización de productos
- Requiere configuración de Google Cloud Project

**Configuración:**
```env
VISION_PROVIDER=google_vision
GOOGLE_VISION_CREDENTIALS=/path/to/google-credentials.json
```

**Precio:**
- 1,000 imágenes/mes: **GRATIS**
- 1,001-5,000,000: $1.50 por 1,000 imágenes
- Aprox. $0.0015 por recibo después del tier gratuito

**Obtener API Key:**
1. Crear proyecto en [Google Cloud Console](https://console.cloud.google.com/)
2. Habilitar Cloud Vision API
3. Crear credenciales de servicio (JSON)
4. Descargar archivo JSON de credenciales

---

### 3. OCR.space ⭐ Mejor opción gratuita

**Descripción:** Servicio de OCR gratuito con generoso tier gratuito.

**Ventajas:**
- ✅ **500 requests/día GRATIS** (~25,000/mes)
- No requiere cuenta para API key de prueba
- Fácil de configurar
- Sin necesidad de tarjeta de crédito

**Desventajas:**
- OCR básico, menos preciso que Claude
- Requiere parsing adicional
- Límite de 5MB por imagen
- PDFs tienen watermark en tier gratuito
- Sin garantías de uptime

**Configuración:**
```env
VISION_PROVIDER=ocrspace
OCRSPACE_API_KEY=helloworld  # Para pruebas, obtén tu propia key
```

**Precio:**
- 500 requests/día: **GRATIS**
- API key "helloworld" disponible para testing rápido
- PRO plan: $6.99/mes para uso ilimitado

**Obtener API Key:** [OCR.space Free API Key](https://ocr.space/ocrapi/freekey)

---

### 4. OpenAI GPT-4o Vision

**Descripción:** Modelo multimodal de OpenAI con capacidades de visión.

**Ventajas:**
- Análisis contextual avanzado
- Buena comprensión de imágenes
- Similar a Claude en precisión
- API bien documentada

**Desventajas:**
- Sin tier gratuito real (solo créditos iniciales)
- Más caro que Google Vision
- Requiere API key de pago

**Configuración:**
```env
VISION_PROVIDER=openai
OPENAI_API_KEY=sk-xxxxx
```

**Precio:**
- Entrada: $5.00 por millón de tokens
- Salida: $20.00 por millón de tokens
- Aprox. $0.02-0.08 por recibo procesado

**Obtener API Key:** [OpenAI Platform](https://platform.openai.com/)

---

## Comparación Rápida

| Proveedor | Tier Gratuito | Precio después | Precisión | Configuración |
|-----------|---------------|----------------|-----------|---------------|
| **Claude** | ❌ No | ~$0.03/recibo | ⭐⭐⭐⭐⭐ | Fácil |
| **Google Vision** | ✅ 1,000/mes | $0.0015/recibo | ⭐⭐⭐⭐ | Media |
| **OCR.space** | ✅ 500/día | $6.99/mes ilimitado | ⭐⭐⭐ | Muy fácil |
| **OpenAI** | ❌ No | ~$0.05/recibo | ⭐⭐⭐⭐⭐ | Fácil |

## Recomendaciones de Uso

### Para Desarrollo y Pruebas
**Usar: OCR.space**
- Generoso tier gratuito (500/día)
- No requiere tarjeta de crédito
- Configuración instantánea

### Para Uso Personal (< 1,000 recibos/mes)
**Usar: Google Cloud Vision**
- 1,000 imágenes gratis al mes
- Buena calidad de OCR
- Infraestructura confiable

### Para Uso Profesional
**Usar: Claude o OpenAI**
- Mejor precisión y categorización
- Análisis contextual inteligente
- Resultados más estructurados

### Para Alto Volumen (> 5,000 recibos/mes)
**Usar: Google Cloud Vision**
- Mejor relación precio/calidad a escala
- $1.50 por 1,000 después del tier gratuito
- Infraestructura probada

## Cambiar de Proveedor

Para cambiar de proveedor, simplemente actualiza la variable `VISION_PROVIDER` en tu archivo `.env`:

```bash
# Cambiar a OCR.space (gratis)
VISION_PROVIDER=ocrspace

# Cambiar a Google Vision (1,000 gratis/mes)
VISION_PROVIDER=google_vision

# Cambiar a Claude (mejor precisión)
VISION_PROVIDER=claude

# Cambiar a OpenAI
VISION_PROVIDER=openai
```

No es necesario reiniciar el servidor, el cambio se aplicará en el siguiente análisis.

## Precisión de Análisis

### Claude y OpenAI (⭐⭐⭐⭐⭐)
- Extracción precisa de productos individuales
- Categorización automática inteligente
- Detección de precios unitarios y totales
- Normalización de nombres de productos
- Detección de descuentos y promociones

### Google Cloud Vision (⭐⭐⭐⭐)
- OCR preciso del texto
- Buena detección de estructura
- Requiere parsing para extraer items individuales
- Categorización básica mediante heurísticas

### OCR.space (⭐⭐⭐)
- OCR básico funcional
- Puede tener errores en texto pequeño
- Requiere parsing y normalización adicional
- Mejor para recibos simples y claros

## Soporte

Si tienes problemas con algún proveedor:
1. Verifica que tu API key esté correctamente configurada
2. Revisa los logs del servidor para mensajes de error
3. Consulta la documentación oficial del proveedor
4. Abre un issue en el repositorio

## Contribuir

¿Quieres agregar soporte para otro proveedor de visión?

1. Crea una nueva clase que herede de `VisionAnalyzer`
2. Implementa el método `analyze_receipt()`
3. Agrega el proveedor a `AnalyzerFactory`
4. Actualiza esta documentación
5. Envía un Pull Request
