# Sistema de Monitorización con Prometheus y Grafana

Sistema simple y eficaz de monitorización usando **Prometheus** para recopilación de métricas y **Grafana** para visualización, con una API Python que expone métricas clave.

## Arquitectura del Sistema

- **API Python**: Endpoints REST simples que exponen métricas de aplicación
- **Prometheus**: Recopila métricas de la API y del sistema (Node Exporter)  
- **Grafana**: Dashboards para visualizar métricas del sistema
- **Node Exporter**: Métricas del sistema operativo (CPU, memoria, disco, red)
- **Grafana Alloy**: Agente moderno para recolección de logs (reemplaza Promtail)
- **Loki**: Almacenamiento y consulta de logs

## Prerrequisitos

- Docker y Docker Compose
- Puertos libres: 3000 (Grafana), 8000 (API), 9090 (Prometheus), 9100 (Node Exporter)

## Instalación y Ejecución

```bash
# Iniciar todos los servicios
./monitor.sh start

# Ver estado de los servicios
./monitor.sh status

# Generar tráfico de prueba para ver métricas
./monitor.sh test
```

## Acceso a los Servicios

| Servicio | URL | Credenciales |
|----------|-----|--------------|
| **Grafana** | http://localhost:3000 | admin / admin123 |
| **Prometheus** | http://localhost:9090 | - |
| **API de Ejemplo** | http://localhost:8000 | - |
| **Node Exporter** | http://localhost:9100 | - |
| **Loki** | http://localhost:3100 | - |
| **Alloy** | http://localhost:12345 | - |

## Dashboards en Grafana

### 1. **Métricas del sistema**
Métricas del servidor desde Node Exporter:
- **CPU**: Uso total del procesador y por núcleo
- **Memoria**: Total, disponible y usada
- **Disco**: Uso en porcentaje por punto de montaje
- **Red**: Tráfico de entrada y salida
- **Carga**: Load average 1m, 5m, 15m
- **Operaciones de disco**: Lecturas y escrituras
- **Procesos**: Running y bloqueados
- **Tiempo de actividad**: Uptime del sistema

### 2. **Métricas de la aplicación**
Métricas de la aplicación Python:
- **Llamadas a la api**: Requests por segundo por endpoint
- **Latencia de respuesta**: Percentiles P50, P95, P99 de respuesta
- **Usuarios en tiempo real**: Usuarios activos simulados
- **Memoria de la aplicación**: Uso de memoria de la app
- **Códigos de estado HTTP**: Distribución de status codes



## API Endpoints

La aplicación expone los siguientes endpoints:

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/` | GET | Información general de la API |
| `/health` | GET | Estado de salud de la aplicación |
| `/users` | GET | Información de usuarios (simula errores 5%) |
| `/data` | GET | Procesamiento de datos (simula latencia variable) |
| `/process` | POST | Procesamiento de datos (simula errores 8%) |
| `/metrics` | GET | Métricas para Prometheus |

## Métricas Monitorizadas

### **Métricas del Sistema (Node Exporter)**
```promql
# CPU
100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)

# Memoria  
(node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100

# Disco
node_filesystem_avail_bytes{mountpoint="/"}

# Red
rate(node_network_receive_bytes_total[5m])
```

### **Métricas de la Aplicación**
```promql
# Requests por segundo
rate(http_requests_total[5m])

# Latencia P95
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Usuarios activos
active_users

# Memoria de la app
app_memory_usage_bytes

# Status codes
sum by(status) (rate(http_requests_total[5m]))
```

## Queries PromQL Útiles

### **Básicas**
```promql
# Ver todas las métricas de la API
{__name__=~"http_.*|active_.*|app_.*"}

# Servicios activos
up

# Requests totales por endpoint
sum by(endpoint) (http_requests_total)
```

### **Análisis de Performance**
```promql
# Endpoints más lentos
topk(5, histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])))

# Tasa de errores por endpoint
rate(http_requests_total{status=~"[45].."}[5m]) / rate(http_requests_total[5m]) * 100

# Carga del sistema vs latencia de la API
100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) and histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

## Probar el Sistema

### **Generar tráfico manualmente**
```bash
# Requests básicos
curl http://localhost:8000/
curl http://localhost:8000/health  
curl http://localhost:8000/users
curl http://localhost:8000/data

# Request POST  
curl -X POST http://localhost:8000/process

# Ver métricas raw
curl http://localhost:8000/metrics
```

### **Generar tráfico automático**
```bash
# Generar 30 requests de prueba
./monitor.sh test

# Generar más tráfico
./monitor.sh test 100
```

## Administración

### **Comandos útiles**
```bash
# Ver logs de un servicio
./monitor.sh logs prometheus
./monitor.sh logs app-ejemplo

# Reiniciar servicios
./monitor.sh restart

# Parar el sistema
./monitor.sh stop

# Ver estado
./monitor.sh status

# Mostrar URLs rápidas
./monitor.sh urls
```

### **Reconstruir la aplicación**
```bash
# Si cambias código de la API
docker-compose build app-ejemplo
docker-compose restart app-ejemplo
```

## Alertas Configuradas

El sistema incluye alertas para:

### **Sistema**
- CPU > 80% por 2+ minutos
- Memoria > 85% por 5+ minutos  
- Disco < 10% disponible

### **Aplicación**
- Servicio caído por 1+ minuto
- Latencia P95 > 1 segundo por 5+ minutos
- Tasa de errores 5xx > 10%

Ver alertas activas en: http://localhost:9090/alerts

## Personalización

### **Agregar nuevos endpoints**
1. Edita `app/app.py`
2. Agrega el decorador `@measure_request`  
3. Reconstruye: `docker-compose build app-ejemplo`

### **Crear nuevos dashboards**
1. Diseña en Grafana UI
2. Exporta como JSON
3. Guarda en `grafana/dashboards/`

### **Modificar métricas**
1. Edita `prometheus/prometheus.yml` 
2. Reinicia: `./monitor.sh restart`

## Logs con Grafana Alloy y Loki

### **Nueva funcionalidad de logs**
El sistema ahora incluye recolección y visualización de logs usando **Grafana Alloy** (reemplaza Promtail) y **Loki**:

- **Grafana Alloy**: Agente moderno que recolecta logs de contenedores Docker
- **Loki**: Almacenamiento eficiente de logs con consultas LogQL
- **Integración completa**: Logs visibles en Grafana junto con métricas

### **Consultas LogQL útiles**
```logql
# Logs de la aplicación Flask
{job="flask-app-logs"}

# Logs de errores
{job="docker-logs"} |= "error"

# Logs por nivel
{job="flask-app-logs"} | json | level="ERROR"

# Logs de los últimos 5 minutos
{job="docker-logs"} [5m]

# Filtrar por contenedor
{job="docker-logs"} |= "app-ejemplo"
```

### **Ver logs en Grafana**
1. Ir a http://localhost:3000
2. Seleccionar "Explore" en el menú lateral
3. Elegir datasource "Loki"
4. Usar queries LogQL para filtrar logs

## Estructura del Proyecto

```
monitorizacion/
├── app/                    # Aplicación Python
│   ├── app.py             # API con métricas
│   ├── Dockerfile         # Imagen Docker
│   └── requirements.txt   # Dependencias
├── grafana/               # Configuración Grafana
│   ├── dashboards/        # Dashboards JSON
│   └── provisioning/      # Auto-configuración
├── prometheus/            # Configuración Prometheus
│   ├── prometheus.yml     # Config principal
│   └── rules/             # Reglas de alertas
├── alloy/                 # Configuración Grafana Alloy
│   └── alloy-config.yaml  # Configuración de logs
├── loki/                  # Configuración Loki
│   └── loki-config.yaml   # Configuración de almacenamiento
├── docker-compose.yml     # Orquestación servicios
├── monitor.sh            # Script de gestión
└── README.md             # Esta documentación
```

## Inicio Rápido

```bash
# 1. Iniciar sistema
./monitor.sh start

# 2. Generar datos
./monitor.sh test

# 3. Ver dashboards
open http://localhost:3000  # Grafana (admin/admin123)

# 4. Ver métricas raw  
open http://localhost:9090  # Prometheus

# 5. Probar API
open http://localhost:8000  # API
```

Sistema listo para monitorización! 