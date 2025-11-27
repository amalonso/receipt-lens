# Scripts de Pruebas

Este directorio contiene scripts para facilitar la ejecución de pruebas.

## Scripts Disponibles

### 🚀 start_test_env.sh
Inicia el entorno de pruebas completo (base de datos + backend).

```bash
./scripts/start_test_env.sh
```

**Qué hace:**
- Detiene cualquier contenedor de pruebas existente
- Levanta PostgreSQL en puerto 5433
- Levanta backend en puerto 8001
- Espera a que los servicios estén listos
- Valida que la API responda

### 🛑 stop_test_env.sh
Detiene el entorno de pruebas.

```bash
./scripts/stop_test_env.sh
```

**Opciones:**
- Puede eliminar volúmenes de base de datos (pregunta interactivamente)

### 🎭 run_e2e_tests.sh
Ejecuta solo las pruebas E2E con Playwright.

```bash
./scripts/run_e2e_tests.sh
```

**Variables de entorno:**
```bash
E2E_BASE_URL=http://localhost:8001  # URL del backend de test
E2E_HEADLESS=true                   # Ejecutar sin ventana del navegador
BROWSER=chromium                     # chromium, firefox, o webkit
```

**Ejemplos:**
```bash
# Con navegador visible
E2E_HEADLESS=false ./scripts/run_e2e_tests.sh

# Con Firefox
BROWSER=firefox ./scripts/run_e2e_tests.sh

# Ralentizado para debugging
E2E_SLOW_MO=1000 E2E_HEADLESS=false ./scripts/run_e2e_tests.sh
```

### 🧪 run_all_tests.sh
Ejecuta TODA la suite de pruebas: unitarias, integración y E2E.

```bash
./scripts/run_all_tests.sh
```

**Qué hace:**
1. Ejecuta pruebas unitarias con cobertura
2. Inicia entorno de test si no está corriendo
3. Ejecuta pruebas E2E
4. Muestra resumen final

## Flujo de Trabajo Típico

### Desarrollo Diario

```bash
# 1. Ejecutar solo pruebas unitarias (rápido)
pytest tests/ -m "not e2e" -v

# 2. Si cambias la interfaz, ejecutar E2E
./scripts/start_test_env.sh      # Solo una vez
./scripts/run_e2e_tests.sh        # Cada vez que quieras probar
```

### Antes de Commit/Push

```bash
# Ejecutar suite completa
./scripts/run_all_tests.sh
```

### Debugging de Pruebas E2E

```bash
# Ver qué está haciendo el navegador
E2E_HEADLESS=false E2E_SLOW_MO=1000 ./scripts/run_e2e_tests.sh

# O ejecutar un test específico
E2E_HEADLESS=false pytest tests/e2e/test_receipt_upload.py::test_upload_and_analyze_single_receipt -v
```

## Troubleshooting

### "Backend not responding"
```bash
# Ver logs
docker-compose -f docker-compose.test.yml logs backend-test

# Reiniciar todo
./scripts/stop_test_env.sh
./scripts/start_test_env.sh
```

### "Database connection error"
```bash
# Limpiar volúmenes y reiniciar
docker-compose -f docker-compose.test.yml down -v
./scripts/start_test_env.sh
```

### Puertos ocupados (8001 o 5433)
```bash
# Ver qué está usando el puerto
lsof -i :8001
lsof -i :5433

# Detener proceso o cambiar puerto en docker-compose.test.yml
```

## Integración con CI/CD

Estos scripts están diseñados para usarse en pipelines de CI/CD:

```yaml
# Ejemplo GitHub Actions
- name: Run tests
  run: |
    ./scripts/start_test_env.sh
    ./scripts/run_all_tests.sh
```

Ver `TESTING.md` para más información sobre CI/CD.
