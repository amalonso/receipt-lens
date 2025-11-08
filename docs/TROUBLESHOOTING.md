# Troubleshooting Guide

## Error 503 al Subir Imágenes

### Síntoma
Cuando intentas subir una imagen de recibo, obtienes un error HTTP 503 (Service Unavailable).

### Causas Comunes

#### 1. Credenciales de Google Vision No Configuradas (Más Común)

Si estás usando `VISION_PROVIDER=google_vision`, este error ocurre cuando:

- El archivo de credenciales JSON no existe en la ruta especificada
- La ruta en `.env` apunta a una ubicación del host que no está montada en Docker
- El archivo no tiene permisos de lectura

**Solución:**

1. **Crea o descarga tu archivo de credenciales de Google Cloud:**
   - Ve a [Google Cloud Console](https://console.cloud.google.com/)
   - Crea un proyecto y habilita la Vision API
   - Crea una cuenta de servicio y descarga el archivo JSON de credenciales

2. **Coloca el archivo en tu proyecto:**
   ```bash
   # Crea una carpeta para credenciales
   mkdir -p /home/user/receipt-lens/credentials

   # Copia tu archivo de credenciales ahí
   cp /ruta/a/tu/google-credentials.json /home/user/receipt-lens/credentials/
   ```

3. **Actualiza tu archivo `.env`:**
   ```bash
   # Dentro del contenedor Docker, la ruta debe apuntar a /app/credentials
   GOOGLE_VISION_CREDENTIALS=/app/credentials/google-credentials.json
   ```

4. **Agrega el volumen en `docker-compose.yml`:**
   ```yaml
   services:
     backend:
       volumes:
         - ./credentials:/app/credentials  # Agrega esta línea
         - ./backend:/app/backend
         - ./frontend:/app/frontend
         - ./uploads:/app/uploads
   ```

5. **Reinicia los contenedores:**
   ```bash
   docker compose down
   docker compose up -d
   ```

#### 2. API Key de Anthropic No Configurada

Si estás usando `VISION_PROVIDER=claude`:

**Solución:**

1. Obtén tu API key de [Anthropic Console](https://console.anthropic.com/)
2. Actualiza tu `.env`:
   ```bash
   ANTHROPIC_API_KEY=sk-ant-your-api-key-here
   ```
3. Reinicia: `docker compose restart backend`

#### 3. Proveedor de Vision Incorrecto

**Solución:**

Verifica que tu proveedor esté correctamente configurado en `.env`:

```bash
# Opciones válidas: claude | google_vision | ocrspace | openai
VISION_PROVIDER=claude
```

### Verificar Configuración

1. **Revisa los logs del backend al iniciar:**
   ```bash
   docker compose logs backend | grep -E "(Vision|ERROR|WARNING)"
   ```

   Deberías ver:
   ```
   INFO - Vision Provider: google_vision
   INFO - Google Vision credentials found at: /app/credentials/google-credentials.json
   INFO - Vision provider validation complete
   ```

2. **Si ves errores como:**
   ```
   ERROR - Google Vision credentials file not found at: /app/credentials/google-credentials.json
   WARNING - Receipt uploads will fail. Please ensure the credentials file exists
   ```

   Esto confirma que el problema es con las credenciales.

### Alternativas si No Quieres Usar Google Vision

Puedes cambiar a otro proveedor:

#### Opción 1: Claude (Anthropic)
```bash
# En .env
VISION_PROVIDER=claude
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

#### Opción 2: OpenAI
```bash
# En .env
VISION_PROVIDER=openai
OPENAI_API_KEY=sk-your-openai-key-here
```

#### Opción 3: OCR.space (Gratis con límites)
```bash
# En .env
VISION_PROVIDER=ocrspace
OCRSPACE_API_KEY=helloworld  # o tu propia key
```

## Otros Errores Comunes

### Error 413: Archivo Demasiado Grande

**Solución:**
Aumenta el límite en `.env`:
```bash
MAX_UPLOAD_SIZE_MB=20
```

### Error 400: Tipo de Archivo No Permitido

**Solución:**
Verifica que tu imagen sea JPG, JPEG, PNG o PDF:
```bash
ALLOWED_EXTENSIONS=jpg,jpeg,png,pdf
```

### La Imagen Se Sube Pero No Se Analiza Correctamente

Si la imagen se sube pero el análisis está vacío o incorrecto:

1. Verifica que la imagen sea clara y legible
2. Prueba con diferentes proveedores de Vision
3. Revisa los logs para ver el texto extraído

## Obtener Ayuda

Si el problema persiste:

1. Revisa los logs completos:
   ```bash
   docker compose logs -f backend
   ```

2. Verifica la configuración:
   ```bash
   docker compose exec backend env | grep -E "(VISION|API_KEY)"
   ```

3. Crea un issue en GitHub con:
   - Los logs del error
   - Tu configuración (sin exponer las API keys)
   - El tipo de imagen que intentas subir
