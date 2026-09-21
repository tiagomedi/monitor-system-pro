#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API simple para sistema de monitorización con Prometheus y Loki
Solo endpoints básicos y métricas esenciales con logging estructurado
"""

import time
import random
import threading
import json
from datetime import datetime
from flask import Flask, request, jsonify
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
import logging
import logging.handlers

# Configuración de logging estructurado para Loki
class StructuredFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'message': record.getMessage(),
            'service': 'app-monitorizacion',
            'version': '1.0.0'
        }
        
        # Agregar campos adicionales si existen
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        if hasattr(record, 'endpoint'):
            log_entry['endpoint'] = record.endpoint
        if hasattr(record, 'method'):
            log_entry['method'] = record.method
        if hasattr(record, 'status_code'):
            log_entry['status_code'] = record.status_code
        if hasattr(record, 'duration'):
            log_entry['duration'] = record.duration
        if hasattr(record, 'ip_address'):
            log_entry['ip_address'] = record.ip_address
            
        return json.dumps(log_entry)

# Configurar logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Handler para consola con formato estructurado
console_handler = logging.StreamHandler()
console_handler.setFormatter(StructuredFormatter())
logger.addHandler(console_handler)

# Inicializar aplicación Flask
app = Flask(__name__)

# Métricas de Prometheus
# Contador para solicitudes HTTP
http_requests_total = Counter(
    'http_requests_total',
    'Total de solicitudes HTTP recibidas',
    ['method', 'endpoint', 'status']
)

# Histograma para duración de solicitudes HTTP
http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'Duración de solicitudes HTTP',
    ['method', 'endpoint']
)

# Gauge para usuarios activos simulados
active_users = Gauge(
    'active_users',
    'Número de usuarios activos en la aplicación'
)

# Gauge para uso de memoria simulado de la aplicación
app_memory_usage_bytes = Gauge(
    'app_memory_usage_bytes',
    'Uso de memoria de la aplicación en bytes'
)

# Contador para operaciones simuladas
api_operations_total = Counter(
    'api_operations_total',
    'Total de operaciones de API',
    ['operation', 'status']
)

def simulate_metrics():
    """
    Función que simula métricas que cambian en segundo plano
    """
    while True:
        try:
            # Simular usuarios activos (entre 5 y 50)
            users = random.randint(5, 50)
            active_users.set(users)
            # Simular uso de memoria (entre 50MB y 200MB)
            memory = random.randint(50 * 1024 * 1024, 200 * 1024 * 1024)
            app_memory_usage_bytes.set(memory)
            # Log de métricas simuladas
            logger.info("Métricas actualizadas", extra={
                'active_users': users,
                'memory_usage_mb': memory // (1024 * 1024),
                'operation': 'metrics_update'
            })
            time.sleep(30)  # Actualizar cada 30 segundos
        except Exception as e:
            logger.error(f"Error actualizando métricas: {e}", extra={
                'operation': 'metrics_update',
                'error': str(e)
            })
            time.sleep(30)

# Decorador para medir duración de solicitudes
def measure_request(f):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        request_id = f"req_{random.randint(1000, 9999)}"
        
        # Log de inicio de request
        logger.info("Inicio de solicitud", extra={
            'request_id': request_id,
            'method': request.method,
            'endpoint': request.endpoint or 'unknown',
            'ip_address': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', 'unknown'),
            'operation': 'request_start'
        })
        
        try:
            response = f(*args, **kwargs)
            status = '200'
            
            # Log de éxito
            duration = time.time() - start_time
            logger.info("Solicitud completada exitosamente", extra={
                'request_id': request_id,
                'method': request.method,
                'endpoint': request.endpoint or 'unknown',
                'status_code': 200,
                'duration': round(duration, 3),
                'operation': 'request_success'
            })
            
            return response
            
        except Exception as e:
            status = '500'
            duration = time.time() - start_time
            
            # Log de error
            logger.error(f"Error en solicitud: {e}", extra={
                'request_id': request_id,
                'method': request.method,
                'endpoint': request.endpoint or 'unknown',
                'status_code': 500,
                'duration': round(duration, 3),
                'error': str(e),
                'operation': 'request_error'
            })
            raise
        finally:
            duration = time.time() - start_time
            endpoint = request.endpoint or 'unknown'
            
            # Registrar métricas
            http_request_duration_seconds.labels(
                method=request.method,
                endpoint=endpoint
            ).observe(duration)
            
            http_requests_total.labels(
                method=request.method,
                endpoint=endpoint,
                status=status
            ).inc()
    
    wrapper.__name__ = f.__name__
    return wrapper

@app.route('/metrics')
def metrics():
    """
    Endpoint para que Prometheus recopile métricas
    """
    logger.info("Métricas solicitadas", extra={
        'operation': 'metrics_endpoint',
        'endpoint': 'metrics'
    })
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

@app.route('/')
@measure_request
def home():
    """
    Endpoint principal de la API
    """
    api_operations_total.labels(operation='home', status='success').inc()
    
    logger.info("Endpoint principal accedido", extra={
        'operation': 'home_endpoint',
        'endpoint': 'home'
    })
    
    return jsonify({
        'service': 'API de Monitorización',
        'status': 'running',
        'version': '1.0.0',
        'endpoints': ['/health', '/users', '/data', '/process', '/logs']
    })

@app.route('/health')
@measure_request
def health():
    """
    Endpoint de verificación de salud
    """
    api_operations_total.labels(operation='health_check', status='success').inc()
    
    uptime = time.time() - app.start_time
    
    logger.info("Health check realizado", extra={
        'operation': 'health_check',
        'endpoint': 'health',
        'uptime_seconds': round(uptime, 2)
    })
    
    return jsonify({
        'status': 'healthy',
        'timestamp': time.time(),
        'uptime': uptime
    })

@app.route('/users')
@measure_request
def get_users():
    """
    Endpoint que simula obtener información de usuarios
    """
    # Simular tiempo de procesamiento
    processing_time = random.uniform(0.1, 0.3)
    time.sleep(processing_time)
    
    # Simular ocasionalmente un error
    if random.random() < 0.05:  # 5% de errores
        api_operations_total.labels(operation='get_users', status='error').inc()
        
        logger.error("Error en obtención de usuarios", extra={
            'operation': 'get_users',
            'endpoint': 'users',
            'error': 'Database connection failed',
            'processing_time': round(processing_time, 3)
        })
        
        return jsonify({'error': 'Database connection failed'}), 500
    
    api_operations_total.labels(operation='get_users', status='success').inc()
    
    active_users_count = int(active_users._value._value)
    total_users = random.randint(100, 500)
    new_users = random.randint(0, 20)
    
    logger.info("Usuarios obtenidos exitosamente", extra={
        'operation': 'get_users',
        'endpoint': 'users',
        'active_users': active_users_count,
        'total_users': total_users,
        'new_users_today': new_users,
        'processing_time': round(processing_time, 3)
    })
    
    return jsonify({
        'active_users': active_users_count,
        'total_users': total_users,
        'new_users_today': new_users
    })

@app.route('/data')
@measure_request 
def get_data():
    """
    Endpoint que simula procesamiento de datos
    """
    # Simular tiempo de procesamiento variable
    processing_time = random.uniform(0.2, 0.8)
    time.sleep(processing_time)
    
    # Simular ocasionalmente latencia alta
    if random.random() < 0.1:  # 10% requests lentos
        extra_delay = random.uniform(1.0, 2.0)
        time.sleep(extra_delay)
        processing_time += extra_delay
        
        logger.warning("Procesamiento lento detectado", extra={
            'operation': 'get_data',
            'endpoint': 'data',
            'processing_time': round(processing_time, 3),
            'extra_delay': round(extra_delay, 3)
        })
    
    api_operations_total.labels(operation='data_processing', status='success').inc()
    
    records_processed = random.randint(100, 1000)
    cache_hit_rate = round(random.uniform(0.7, 0.95), 2)
    
    logger.info("Datos procesados exitosamente", extra={
        'operation': 'get_data',
        'endpoint': 'data',
        'records_processed': records_processed,
        'processing_time_ms': int(processing_time * 1000),
        'cache_hit_rate': cache_hit_rate
    })
    
    return jsonify({
        'records_processed': records_processed,
        'processing_time_ms': int(processing_time * 1000),
        'cache_hit_rate': cache_hit_rate
    })

@app.route('/process', methods=['POST'])
@measure_request
def process_data():
    """
    Endpoint POST que simula procesamiento de datos
    """
    # Simular validación de datos
    processing_time = random.uniform(0.1, 0.4)
    time.sleep(processing_time)
    
    # Simular errores de validación ocasionalmente
    if random.random() < 0.08:  # 8% de errores
        api_operations_total.labels(operation='process_data', status='error').inc()
        
        logger.error("Error en procesamiento de datos", extra={
            'operation': 'process_data',
            'endpoint': 'process',
            'error': 'Invalid data format',
            'processing_time': round(processing_time, 3)
        })
        
        return jsonify({'error': 'Invalid data format'}), 400
    
    api_operations_total.labels(operation='process_data', status='success').inc()
    
    job_id = f"job_{random.randint(1000, 9999)}"
    
    logger.info("Datos procesados exitosamente", extra={
        'operation': 'process_data',
        'endpoint': 'process',
        'job_id': job_id,
        'processing_time': round(processing_time, 3)
    })
    
    return jsonify({
        'result': 'processed',
        'job_id': job_id,
        'estimated_completion': '2-5 minutes'
    })

@app.route('/logs')
@measure_request
def generate_test_logs():
    """
    Endpoint para generar logs de prueba con diferentes niveles
    """
    log_levels = ['INFO', 'WARNING', 'ERROR', 'DEBUG']
    
    for i in range(5):
        level = random.choice(log_levels)
        message = f"Log de prueba {i+1} - Nivel: {level}"
        
        if level == 'INFO':
            logger.info(message, extra={
                'operation': 'test_logs',
                'log_number': i+1,
                'level': level
            })
        elif level == 'WARNING':
            logger.warning(message, extra={
                'operation': 'test_logs',
                'log_number': i+1,
                'level': level
            })
        elif level == 'ERROR':
            logger.error(message, extra={
                'operation': 'test_logs',
                'log_number': i+1,
                'level': level
            })
        elif level == 'DEBUG':
            logger.debug(message, extra={
                'operation': 'test_logs',
                'log_number': i+1,
                'level': level
            })
        
        time.sleep(0.1)
    
    logger.info("Logs de prueba generados", extra={
        'operation': 'generate_test_logs',
        'endpoint': 'logs',
        'logs_generated': 5
    })
    
    return jsonify({
        'message': 'Logs de prueba generados',
        'logs_count': 5,
        'levels': log_levels
    })

@app.errorhandler(404)
def not_found(error):
    """
    Manejador de errores 404
    """
    http_requests_total.labels(
        method=request.method,
        endpoint='not_found',
        status='404'
    ).inc()
    
    logger.warning("Endpoint no encontrado", extra={
        'operation': 'not_found',
        'method': request.method,
        'endpoint': request.path,
        'status_code': 404
    })
    
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """
    Manejador de errores 500
    """
    http_requests_total.labels(
        method=request.method,
        endpoint=request.endpoint or 'unknown',
        status='500'
    ).inc()
    
    logger.error("Error interno del servidor", extra={
        'operation': 'internal_error',
        'method': request.method,
        'endpoint': request.endpoint or 'unknown',
        'status_code': 500,
        'error': str(error)
    })
    
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Tiempo de inicio para calcular uptime
    app.start_time = time.time()
    
    # Iniciar hilo en segundo plano para métricas simuladas
    metrics_thread = threading.Thread(target=simulate_metrics, daemon=True)
    metrics_thread.start()
    
    logger.info("Iniciando API de monitorización en puerto 8000", extra={
        'operation': 'app_startup',
        'port': 8000,
        'version': '1.0.0'
    })
    logger.info("Métricas disponibles en http://localhost:8000/metrics", extra={
        'operation': 'app_startup',
        'metrics_endpoint': '/metrics'
    })
    logger.info("Endpoints: /, /health, /users, /data, /process, /logs", extra={
        'operation': 'app_startup',
        'available_endpoints': ['/', '/health', '/users', '/data', '/process', '/logs']
    })
    
    # Ejecutar aplicación Flask
    app.run(host='0.0.0.0', port=8000, debug=False) 