import os
import os
import tempfile
import shutil
import logging
import requests
import json
import time
import schedule
from typing import Dict, List, Any, Optional
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.keys import Keys
import pywhatkit as pwk
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

logger = logging.getLogger(__name__)

class WhatsAppSender:

    # class for sending WhatsApp messages using Twilio API

    def __init__(self):

        # initialize sender

        self.config = self._load_config()
        self.twilio_client = None
        self.selenium_driver = None
        self._temp_profile_dir: Optional[str] = None
        self._initialize_twilio_client()    

    def _load_config(self) -> Dict[str, Any]:

       # config loader

        # Read environment configuration. Normalize and strip whitespace.
        config = {
            
            'send_method': (os.getenv('WHATSAPP_METHOD') or 'simulation').strip(),
            # allow both names for destination to be flexible
            'destination_whatsapp': (os.getenv('WHATSAPP_DESTINY') or os.getenv('DESTINATION_WHATSAPP') or '').strip(),

            # 1. twilio config
            'twilio_account_sid': os.getenv('TWILIO_ACCOUNT_SID', '').strip() or None,
            'twilio_auth_token': os.getenv('TWILIO_AUTH_TOKEN', '').strip() or None,
            'twilio_whatsapp_from': os.getenv('TWILIO_WHATSAPP_FROM', '').strip() or None,

            # 2. selenium config
            'chrome_driver_path': os.getenv('CHROME_DRIVER_PATH', '/usr/local/bin/chromedriver'),
            'whatsapp_web_delay': int(os.getenv('WHATSAPP_WEB_DELAY', '90')),
            # Optional Chrome user data dir (to persist WhatsApp Web session). If not set, a temp profile will be used per run.
            'whatsapp_profile_dir': (os.getenv('WHATSAPP_PROFILE_DIR') or '').strip() or None,

            # 3. general config
            'max_retries': int(os.getenv('WHATSAPP_MAX_RETRIES', '3')),
            'wait_time': int(os.getenv('WHATSAPP_WAIT_TIME', '5')),

        }

        logger.info("Configuracion del WhatsAppSender cargada.")
        return config
    
    # initialize Twilio client

    def _initialize_twilio_client(self):
        
        # if credentials are available, initialize client
        if (self.config['twilio_account_sid'] and 
            self.config['twilio_auth_token'] and
            self.config['twilio_whatsapp_from']):

            try:

                self.twilio_client = Client(
                    self.config['twilio_account_sid'], 
                    self.config['twilio_auth_token']
                )
                logger.info("Cliente de Twilio inicializado con éxito.")
            except Exception as e:
                logger.error(f"Error al inicializar el cliente de Twilio: {str(e)}")
                self.twilio_client = None
    
    # METHOD 1: send message using twilio API

    def send_twilio_message(self, message: str, destiny: str, linked_file: List[str] = None) -> bool:

        try: 
            if not self.twilio_client:
                logger.error("El cliente de Twilio no está inicializado.")
                return False

            # format whatsapp numbers

            from_whatsapp = f'whatsapp:{self.config["twilio_whatsapp_from"]}'
            to_whatsapp = f'whatsapp:{destiny}'

            # send message
            message_params = {
                'body': message,
                'from_': from_whatsapp,
                'to': to_whatsapp
            }

            # add url if exists

            if linked_file:
                message_params['media_url'] = linked_file

            # send message

            message = self.twilio_client.messages.create(**message_params)

            logger.info(f"Mensaje enviado via Twilio a {destiny}. SID: {message.sid}")
            logger.info(f"Estado del mensaje: {message.status}")

            # verify status
            time.sleep(2)
            message = message.fetch()
            logger.info(f"📊 Estado actualizado: {message.status}")

            return message.status in ['queued', 'sent', 'delivered']
   
        except TwilioRestException as e:
            logger.error(f"Error de twilio {e}")
            return False
        except Exception as e:
            logger.error(f"Error inesperado en Twilio: {e}")
            return False
        
    # METHOD 2: send message using PYWHATKIT 

    def send_pywhatkit_message(self, message: str, destiny: str) -> bool:

        try:
            # format destiny
            clean_destiny = destiny.replace('+', '').strip()

            # get current time
            right_now = datetime.now()
            hour = right_now.hour
            minute = right_now.minute + 2

            if minute >= 60:
                hour += 1
                minute -= 60

            # send message
            pwk.sendwhatmsg(f"+{clean_destiny}", message, hour, minute, wait_time=15)

            logger.info(f"Mensaje enviado via pywhatkit a {destiny}.")
            return True
        
        except Exception as e:
            logger.error(f"Error enviando mensaje via pywhatkit: {e}")
            return False

    #METHOD 3: send message using SELENIUM

    def initialize_selenium(self) -> bool:

        try: 
            chrome_options = Options()

            # Choose Chrome profile directory
            profile_dir = self.config.get('whatsapp_profile_dir')
            if profile_dir:
                os.makedirs(profile_dir, exist_ok=True)
                chrome_options.add_argument(f"--user-data-dir={profile_dir}")
                logger.info(f"Usando perfil persistente de Chrome en: {profile_dir}")
            else:
                # Use a unique temporary profile per run to avoid 'already in use' locks
                self._temp_profile_dir = tempfile.mkdtemp(prefix="wa_profile_")
                chrome_options.add_argument(f"--user-data-dir={self._temp_profile_dir}")
                logger.info(f"Usando perfil temporal de Chrome en: {self._temp_profile_dir}")

            # config for better performance
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)

            # Resolve ChromeDriver path
            driver_path = self.config.get('chrome_driver_path')
            service: Optional[Service] = None

            try:
                # Prefer explicit path if it exists
                if driver_path and os.path.exists(driver_path):
                    service = Service(driver_path)
                else:
                    # Fallback to webdriver-manager to download the correct driver
                    from webdriver_manager.chrome import ChromeDriverManager
                    resolved_path = ChromeDriverManager().install()
                    # Validate resolved path on Windows must point to chromedriver.exe
                    use_service = True
                    if os.name == 'nt':
                        use_service = resolved_path.lower().endswith('chromedriver.exe') and os.path.isfile(resolved_path)
                    else:
                        use_service = os.path.isfile(resolved_path)

                    if use_service:
                        service = Service(resolved_path)
                        logger.info(f"ChromeDriver resuelto via webdriver-manager: {resolved_path}")
                    else:
                        # Let Selenium Manager resolve it if path seems incorrect
                        service = None
                        logger.warning(f"Ruta de ChromeDriver sospechosa ({resolved_path}); se usará Selenium Manager para resolver el driver.")
            except Exception as e:
                logger.warning(f"No se pudo resolver ChromeDriver: {e}. Intentando inicializar sin ruta explícita...")

            # init driver (Service is preferred in Selenium 4)
            if service is not None:
                self.selenium_driver = webdriver.Chrome(service=service, options=chrome_options)
            else:
                # Last resort: rely on PATH
                self.selenium_driver = webdriver.Chrome(options=chrome_options)

            # open whatsapp web
            self.selenium_driver.get("https://web.whatsapp.com")

            # wait for manual QR scan
            logger.info("Por favor, escanee el código QR en WhatsApp Web.")
            WebDriverWait(self.selenium_driver, self.config['whatsapp_web_delay']).until(
                EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@data-tab="3"]'))
            )

            logger.info("WhatsApp Web listo para enviar mensajes.")
            return True
        
        except Exception as e:
            logger.error(f"Error inicializando Selenium: {e}")
            return False
    
    def send_selenium_message(self, message: str, destiny: str) -> bool:

        try: 
            # init driver if not ready
            if not self.selenium_driver:
                if not self.initialize_selenium():
                    return False
            
            # Prefer direct chat open by phone number to handle unsaved contacts
            clean_number = destiny.replace('+', '').replace(' ', '').strip()
            self.selenium_driver.get(f"https://web.whatsapp.com/send?phone={clean_number}")

            # Wait for chat UI to be ready and find the message input robustly
            message_box = None
            wait = WebDriverWait(self.selenium_driver, 30)
            try:
                # Newer WhatsApp web selector hierarchy
                message_box = wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="conversation-compose-box-input"] div[contenteditable="true"]'))
                )
            except TimeoutException:
                # Fallback to older selectors with data-tab variations
                candidates = [
                    '//div[@contenteditable="true"][@data-tab="10"]',
                    '//div[@contenteditable="true"][@data-tab="6"]',
                    '//div[@contenteditable="true"][@data-tab="9"]',
                    '//footer//div[@contenteditable="true"]'
                ]
                for xp in candidates:
                    try:
                        message_box = wait.until(EC.presence_of_element_located((By.XPATH, xp)))
                        if message_box:
                            break
                    except TimeoutException:
                        continue

            if not message_box:
                raise TimeoutException("No se encontró el cuadro de mensaje de WhatsApp Web")

            # write and send message with ENTER (more robust than clicking send button)
            message_box.click()
            time.sleep(0.3)
            message_box.send_keys(message)
            time.sleep(0.3)
            message_box.send_keys(Keys.ENTER)

            logger.info(f"Mensaje enviado via Selenium a {destiny}.")
            return True
        except Exception as e:
            try:
                # Try to capture a screenshot for debugging
                os.makedirs('outputs', exist_ok=True)
                screenshot_path = os.path.join('outputs', f'wa_error_{int(time.time())}.png')
                if self.selenium_driver:
                    self.selenium_driver.save_screenshot(screenshot_path)
                    logger.error(f"Error enviando mensaje via Selenium: {e}. Screenshot: {screenshot_path}")
                else:
                    logger.error(f"Error enviando mensaje via Selenium: {e}")
            except Exception:
                logger.error(f"Error enviando mensaje via Selenium: {e}")
            return False
        
    def close_selenium(self):
        if self.selenium_driver:
            self.selenium_driver.quit()
            self.selenium_driver = None
            logger.info("Selenium WebDriver cerrado.")
        # Cleanup temporary profile directory if we created one
        if getattr(self, '_temp_profile_dir', None):
            try:
                shutil.rmtree(self._temp_profile_dir, ignore_errors=True)
                logger.info(f"Perfil temporal de Chrome eliminado: {self._temp_profile_dir}")
            except Exception as e:
                logger.warning(f"No se pudo eliminar el perfil temporal de Chrome: {e}")
            finally:
                self._temp_profile_dir = None

    # METHOD 4: simulate send message

    def simulate_send_message(self, message: str, destiny: str) -> bool:

        try: 
            logger.info("MODO SIMULACION")
            logger.info(f"Destino: {destiny}")
            logger.info(f"Mensaje: {message}")
            logger.info("Mensaje simulado enviado con éxito.")

            # save file log

            os.makedirs('outputs', exist_ok=True)
            with open('outputs/simulation_log.txt', 'w', encoding='utf-8') as f:
                f.write(f"=== {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")
                f.write(f"Destino: {destiny}\n")
                f.write(f"Mensaje: {message}\n")
                f.write("="*50 + "\n")

            return True
    
        except Exception as e:
            logger.error(f"Error en la simulación de envío de mensaje: {e}")
            return False
        

    # MAIN SEND METHOD

    def send_message(self, message: str, destiny: str = None, retry: bool = True) -> bool:

        if not destiny:
            destiny = self.config['destination_whatsapp']

        if not destiny:
            logger.error("No se ha proporcionado un destino para el mensaje de WhatsApp.")
            return False
        
        method = self.config['send_method'].lower()
        max_retries = self.config['max_retries'] if retry else 1

        for attempt in range(max_retries):

            try:

                logger.info(f"Intentando envío (intento {attempt + 1}/{max_retries})...")

                if method == 'twilio':
                    result = self.send_twilio_message(message, destiny)
                elif method == 'pywhatkit':
                    result = self.send_pywhatkit_message(message, destiny)
                elif method == 'selenium':
                    result = self.send_selenium_message(message, destiny)
                else:  # simulation
                    result = self.simulate_send_message(message, destiny)

                if result:
                    return True
                else:
                    logger.warning(f"Intento {attempt + 1} fallido.")
                    if attempt < max_retries - 1:
                        time.sleep(self.config['wait_time'])

            except Exception as e:
                logger.error(f"Error en el intento {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                        time.sleep(self.config['wait_time'])

        logger.error("Todos los intentos de envío han fallado.")
        return False

    # send summary

    def send_summary(self, results: Dict[str, Any], destiny: str= None) -> bool:

        try: 

            message = self._format_summary(results)
            return self.send_message(message, destiny)
        
        except Exception as e:
            logger.error(f"Error enviando resumen: {e}")
            return False
    
    # send whatsapp graph 

    def send_graph(self, results: Dict[str, Any], destiny: str= None) -> bool:

        try:
            graph_message ="""

Graficos Generados:

Se han generado varios graficos para visualizar el analisis de ventas.
Puede encontrarlos en la carpeta 'outputs/graphs' del proyecto.

"""
            return self.send_message(graph_message, destiny)
        except Exception as e:
            logger.error(f"Error enviando graficos: {e}")
            return False
        
    # format summary message
    def _format_summary(self, results: Dict[str, Any]) -> str:

        try:
            metrics = results['summary_metrics']
            top_models = results['top_models'].index[0]
            top_headquarter = results['sales_by_headquarter'].index[0]
            top_channel = results['sales_by_channel'].index[0]

            # Flatten into one paragraph
            parts = []
            parts.append("Reporte de análisis de ventas.")
            parts.append(
                f"Clientes únicos: {metrics['unique_clients']:,}. "
                f"Total de ventas: {metrics['total_sales']:,}. "
                f"Ventas totales sin IGV: ${metrics['total_sales_without_igv']:,.2f}. "
                f"Ventas totales con IGV: ${metrics['total_sales_with_igv']:,.2f}. "
                f"IGV total recaudado: ${metrics['total_igv_collected']:,.2f}. "
                f"Venta promedio: ${metrics['average_sales_without_igv']:,.2f}."
            )
            parts.append(
                f"Modelo más vendido: {top_models}. "
                f"Sede con más ventas: {top_headquarter}. "
                f"Canal con más ventas: {top_channel}."
            )

            # sales by headquarter inline
            hq_details = ", ".join([f"{hq}: ${sales:,.2f}" for hq, sales in results['sales_by_headquarter'].items()])
            parts.append(f"Ventas por sede: {hq_details}.")

            # top 5 models inline
            top5 = []
            for i, (model, sales) in enumerate(results['top_models'].items(), 1):
                top5.append(f"{i}) {model}: ${sales:,.2f}")
                if i >= 5:
                    break
            parts.append("Top 5 modelos: " + "; ".join(top5) + ".")

            parts.append(f"Generado: {self._get_today_date()}.")

            return " ".join(parts)
        
        except Exception as e:
            logger.error(f"Error formateando resumen: {e}")
            return "Error formateando resumen."
        
    # get today date
    def _get_today_date(self) -> str:
        
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # send full report

    def send_full_report(self, results: Dict[str, Any], destiny: str = None) -> bool:

        try:
            if not destiny:
                destiny = self.config['destination_whatsapp']
            
            if not destiny:
                logger.error("No se ha proporcionado un destino para el mensaje de WhatsApp.")
                return False

            logger.info(f"Enviando reporte completo a {destiny}...")

            # Build a single-paragraph message combining summary and graph note
            message = self._format_summary(results)
            message += "  Los gráficos del análisis se guardaron en la carpeta outputs/graphs."

            success = self.send_message(message, destiny)

            # close selenium if used
            if self.config['send_method'] == 'selenium':
                self.close_selenium()

            return success
        
        except Exception as e:
            logger.error(f"Error enviando reporte completo: {e}")
            # close selenium if error
            if self.config['send_method'] == 'selenium':
                self.close_selenium()
            return False
        
# aux function for direct use
def send_whatsapp_report(results: Dict[str, Any], destiny: str= None) -> bool:

    try:
        sender = WhatsAppSender()
        return sender.send_full_report(results, destiny)
    except Exception as e:
        logging.error(f"Error enviando reporte de WhatsApp: {e}")
        return False