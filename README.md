# RPA de WhatsApp para Análisis de Ventas 📊

Aplicación en Python que carga datos de ventas, realiza un análisis consolidado, genera gráficas y envía un reporte por WhatsApp a través de Twilio.

- Carga y validación de datos desde Excel (`data/Ventas_Fundamentos.xlsx`)
- Métricas clave y top de modelos, sedes y canales
- Generación de gráficas en `outputs/graphs/`
- Envío de reporte vía WhatsApp con Twilio
- Hosting opcional de imágenes en imgbb (URLs públicas para adjuntar en WhatsApp)
- Fallback automático a simulación si Twilio retorna límite diario (error `63038`)

---

## Requisitos previos ⚙️

- Python 3.10 o superior
- Windows recomendado (probado en PowerShell). Funciona en otros SO con Python.
- Cuenta de Twilio con WhatsApp habilitado (número de envío) – para envíos reales
- Cuenta en imgbb (opcional) para alojar las imágenes

Dependencias se instalan desde `requirements.txt`.

---

## Instalación 📦
En **PowerShell** (Windows):

```powershell
# 1) Clonar el repositorio
# git clone https://github.com/<tu-usuario>/<repo>.git
# cd <repo>

# 2) Crear y activar entorno virtual (opcional pero recomendado)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3) Instalar dependencias
pip install -r requirements.txt

# Alternativa: instalar con script auxiliar
python install_dependencies.py
```

---

## Configuración 🔧

Se usa python-dotenv y un archivo `whatsapp_config.env` (no se versiona). Toma como base `whatsapp_config.env.sample`.

Variables principales:

- `WHATSAPP_DESTINY` — Número E.164 de destino (ej: `+1234567890`)
- `TWILIO_ACCOUNT_SID` — SID de la cuenta Twilio
- `TWILIO_AUTH_TOKEN` — Token de autenticación Twilio
- `TWILIO_WHATSAPP_FROM` — Número WhatsApp de Twilio en formato E.164 (sin el prefijo `whatsapp:`)
- `IMGBB_API_KEY` (opcional) — API key de imgbb para subir imágenes
- `WHATSAPP_MAX_RETRIES` (opcional) — Reintentos en fallas transitorias (default `3`)
- `WHATSAPP_WAIT_TIME` (opcional) — Espera entre reintentos en segundos (default `5`)

---

## Puesta en marcha rápida 🚀

1) Crear o verificar los datos de ejemplo (si no tienes el Excel):

```powershell
python create_sample_data.py
```

2) Ejecutar el proceso RPA:

```powershell
python main.py
```

El flujo realiza:
- Carga y validación de `data/Ventas_Fundamentos.xlsx`
- Análisis y métricas (clientes, ventas, topes)
- Generación de gráficas en `outputs/graphs/`
- Envío del reporte por WhatsApp (Twilio). Si el límite diario está excedido, se simula y se incluyen las URLs de imgbb.

---

## Flujo de trabajo 🧭

1) Cargar y validar datos (estructura esperada por `utils/data_loader.py`).
2) Analizar datos (cálculos en `utils/analyzer.py`).
3) Generar gráficas (salvan en `outputs/graphs/` con `utils/visualizer.py`).
4) Enviar reporte por WhatsApp (texto + URLs de imágenes) con `utils/whatsapp_sender.py`.

---

## Estructura del proyecto 📁

```
main.py                         # Orquestación del flujo
create_sample_data.py           # Genera Excel de ejemplo si no existe
requirements.txt                # Dependencias
whatsapp_config.env.sample      # Variables de entorno (plantilla)

utils/
  data_loader.py                # Carga/validación de datos
  analyzer.py                   # Métricas y agregados
  visualizer.py                 # Gráficas a outputs/graphs
  whatsapp_sender.py            # Envío WhatsApp con Twilio + fallback simulación
  image_uploader.py             # Subida a imgbb

experimental/
  whatsapp_sender_experimental.py  # Implementaciones archivadas (Selenium/pywhatkit) – no producción

outputs/
  graphs/                       # PNG/JPG de las visualizaciones
  simulation_log.txt            # Bitácora de simulaciones
  simulation_message.txt        # Cuerpo de mensaje simulado
```

---

## Salidas 📤

- Gráficas: `outputs/graphs/*.png|jpg|jpeg`.
- Mensaje simulado: `outputs/simulation_message.txt`.
- Log de simulación: `outputs/simulation_log.txt` (histórico con timestamp).

---

## Twilio y límites ⏳

- Si Twilio retorna `63038` (límite diario), el sistema:
  1) Detiene reintentos inútiles.
  2) Sube las gráficas a imgbb (si `IMGBB_API_KEY` está configurada) y arma el mensaje con todas las URLs.
  3) Escribe el mensaje simulado en `outputs/simulation_message.txt` y la bitácora en `outputs/simulation_log.txt`.

Para levantar el límite: espera el reinicio de la ventana de 24h o contacta a Soporte de Twilio para aumentar el cupo (cuenta verificada, caso de uso, volúmenes esperados, opt-in, etc.).

---

## Solución de problemas 🧩

- WhatsApp no envía (Twilio): verifica credenciales, que el número tenga WhatsApp habilitado y que no estés en sandbox. Revisa límites de cuenta.
- Sin imágenes en el mensaje: asegúrate de tener archivos en `outputs/graphs/` y configurar `IMGBB_API_KEY`.
- Error al leer Excel: manten `openpyxl >= 3.1.0`. El archivo de ejemplo se genera con `create_sample_data.py`.

---

## Notas de seguridad 🔒

- `whatsapp_config.env` está ignorado por Git. Usa la plantilla `whatsapp_config.env.sample` y no subas credenciales.
- Archivos generados en `outputs/` y `data/` están en `.gitignore` para evitar subir datos sensibles.

---

## Créditos 🙌

- [Twilio](https://www.twilio.com/) para el envío de WhatsApp
- [pandas](https://pandas.pydata.org/) y [matplotlib](https://matplotlib.org/) para análisis y visualización
- [imgbb](https://api.imgbb.com/) para alojar imágenes públicas
