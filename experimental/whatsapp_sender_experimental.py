"""
Experimental WhatsApp sender implementations (archived).

This module preserves the previous multi-method sender (Twilio, pywhatkit, Selenium,
and simulation) for reference and future experimentation. It's not imported by the
main application anymore. The active sender is now Twilio-only in `utils/whatsapp_sender.py`.

Note: These implementations may require additional dependencies (selenium, pywhatkit,
webdriver-manager) which are no longer installed by default.
"""

import logging
from typing import Dict, List, Any, Optional

# The original class was kept verbatim for experimentation purposes.
# It depends on selenium and pywhatkit which are no longer part of the default runtime.

try:
    import os
    import tempfile
    import shutil
    import time
    import urllib.parse
    from datetime import datetime
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.common.exceptions import TimeoutException
    from selenium.webdriver.common.keys import Keys
    import pywhatkit as pwk
    from twilio.rest import Client
    from twilio.base.exceptions import TwilioRestException
except Exception as _e:  # pragma: no cover - experimental only
    pass


logger = logging.getLogger(__name__)


class ExperimentalWhatsAppSender:
    """Original WhatsApp sender with Selenium/pywhatkit methods (for reference)."""

    def __init__(self):
        self.config = self._load_config()
        self.twilio_client = None
        self.selenium_driver = None
        self._temp_profile_dir: Optional[str] = None
        self._initialize_twilio_client()

    def _load_config(self) -> Dict[str, Any]:
        config = {
            'send_method': (os.getenv('WHATSAPP_METHOD') or 'simulation').strip(),
            'destination_whatsapp': (os.getenv('WHATSAPP_DESTINY') or os.getenv('DESTINATION_WHATSAPP') or '').strip(),
            'twilio_account_sid': os.getenv('TWILIO_ACCOUNT_SID', '').strip() or None,
            'twilio_auth_token': os.getenv('TWILIO_AUTH_TOKEN', '').strip() or None,
            'twilio_whatsapp_from': os.getenv('TWILIO_WHATSAPP_FROM', '').strip() or None,
            'chrome_driver_path': os.getenv('CHROME_DRIVER_PATH', '/usr/local/bin/chromedriver'),
            'whatsapp_web_delay': int(os.getenv('WHATSAPP_WEB_DELAY', '90')),
            'whatsapp_profile_dir': (os.getenv('WHATSAPP_PROFILE_DIR') or '').strip() or None,
            'selenium_headless': (os.getenv('WHATSAPP_HEADLESS', 'false').strip().lower() == 'true'),
            'selenium_hide_window': (os.getenv('WHATSAPP_HIDE_WINDOW', 'true').strip().lower() == 'true'),
            'max_retries': int(os.getenv('WHATSAPP_MAX_RETRIES', '3')),
            'wait_time': int(os.getenv('WHATSAPP_WAIT_TIME', '5')),
        }
        logger.info("Configuracion del WhatsAppSender (experimental) cargada.")
        return config

    def _initialize_twilio_client(self):
        if (self.config.get('twilio_account_sid') and 
            self.config.get('twilio_auth_token') and
            self.config.get('twilio_whatsapp_from')):
            try:
                self.twilio_client = Client(
                    self.config['twilio_account_sid'], 
                    self.config['twilio_auth_token']
                )
                logger.info("Cliente de Twilio inicializado con éxito (experimental).")
            except Exception as e:
                logger.error(f"Error al inicializar el cliente de Twilio: {str(e)}")
                self.twilio_client = None

    # --- Experimental pywhatkit and Selenium methods ---
    def send_pywhatkit_message(self, message: str, destiny: str) -> bool:  # pragma: no cover - experimental
        try:
            clean_destiny = destiny.replace('+', '').strip()
            wt = max(10, int(self.config.get('pywhatkit_wait_time', 25)))
            ct = max(3, int(self.config.get('pywhatkit_close_time', 5)))
            tc = bool(self.config.get('pywhatkit_tab_close', False))
            logger.info(f"pywhatkit: wait_time={wt}s, tab_close={tc}, close_time={ct}s")
            pwk.sendwhatmsg_instantly(f"+{clean_destiny}", message, wait_time=wt, tab_close=tc, close_time=ct)
            if not tc:
                time.sleep(ct + 2)
            logger.info(f"Mensaje enviado via pywhatkit a {destiny}.")
            return True
        except Exception as e:
            logger.error(f"Error enviando mensaje via pywhatkit: {e}")
            return False

    def initialize_selenium(self) -> bool:  # pragma: no cover - experimental
        try:
            chrome_options = Options()
            profile_dir = self.config.get('whatsapp_profile_dir')
            if profile_dir:
                os.makedirs(profile_dir, exist_ok=True)
                chrome_options.add_argument(f"--user-data-dir={profile_dir}")
                logger.info(f"Usando perfil persistente de Chrome en: {profile_dir}")
            else:
                self._temp_profile_dir = tempfile.mkdtemp(prefix="wa_profile_")
                chrome_options.add_argument(f"--user-data-dir={self._temp_profile_dir}")
                logger.info(f"Usando perfil temporal de Chrome en: {self._temp_profile_dir}")

            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.page_load_strategy = 'eager'
            if self.config.get('selenium_headless'):
                chrome_options.add_argument("--headless=new")
                chrome_options.add_argument("--disable-gpu")
                chrome_options.add_argument("--window-size=1280,900")
            elif self.config.get('selenium_hide_window'):
                chrome_options.add_argument("--window-size=320,200")
                chrome_options.add_argument("--window-position=2000,2000")

            driver_path = self.config.get('chrome_driver_path')
            service: Optional[Service] = None
            try:
                if driver_path and os.path.exists(driver_path):
                    service = Service(driver_path)
                else:
                    from webdriver_manager.chrome import ChromeDriverManager
                    resolved_path = ChromeDriverManager().install()
                    use_service = True
                    if os.name == 'nt':
                        use_service = resolved_path.lower().endswith('chromedriver.exe') and os.path.isfile(resolved_path)
                    else:
                        use_service = os.path.isfile(resolved_path)
                    if use_service:
                        service = Service(resolved_path)
                        logger.info(f"ChromeDriver resuelto via webdriver-manager: {resolved_path}")
                    else:
                        service = None
                        logger.warning(f"Ruta de ChromeDriver sospechosa ({resolved_path}); se usará Selenium Manager para resolver el driver.")
            except Exception as e:
                logger.warning(f"No se pudo resolver ChromeDriver: {e}. Intentando inicializar sin ruta explícita...")

            if service is not None:
                self.selenium_driver = webdriver.Chrome(service=service, options=chrome_options)
            else:
                self.selenium_driver = webdriver.Chrome(options=chrome_options)

            self.selenium_driver.get("https://web.whatsapp.com")
            logger.info("Por favor, escanee el código QR en WhatsApp Web.")
            WebDriverWait(self.selenium_driver, self.config['whatsapp_web_delay']).until(
                EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@data-tab="3"]'))
            )
            logger.info("WhatsApp Web listo para enviar mensajes.")
            return True
        except Exception as e:
            logger.error(f"Error inicializando Selenium: {e}")
            return False

    def send_selenium_message(self, message: str, destiny: str) -> bool:  # pragma: no cover - experimental
        try:
            if not self.selenium_driver:
                if not self.initialize_selenium():
                    return False
            clean_number = destiny.replace('+', '').replace(' ', '').strip()
            prefilled_text = urllib.parse.quote(message)
            self.selenium_driver.get(f"https://web.whatsapp.com/send?phone={clean_number}&text={prefilled_text}")
            message_box = None
            wait = WebDriverWait(self.selenium_driver, 30)
            try:
                message_box = wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="conversation-compose-box-input"] div[contenteditable="true"]'))
                )
            except TimeoutException:
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
            try:
                send_btn = WebDriverWait(self.selenium_driver, 12).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-testid="compose-btn-send"]'))
                )
                send_btn.click()
            except TimeoutException:
                try:
                    self.selenium_driver.execute_script("arguments[0].focus(); arguments[0].scrollIntoView(true);", message_box)
                    message_box.click()
                    time.sleep(0.2)
                    message_box.send_keys(Keys.ENTER)
                except Exception:
                    pass
            logger.info(f"Mensaje enviado via Selenium a {destiny}.")
            return True
        except Exception as e:
            try:
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

    def close_selenium(self):  # pragma: no cover - experimental
        if self.selenium_driver:
            self.selenium_driver.quit()
            self.selenium_driver = None
            logger.info("Selenium WebDriver cerrado.")
        if getattr(self, '_temp_profile_dir', None):
            try:
                shutil.rmtree(self._temp_profile_dir, ignore_errors=True)
                logger.info(f"Perfil temporal de Chrome eliminado: {self._temp_profile_dir}")
            except Exception as e:
                logger.warning(f"No se pudo eliminar el perfil temporal de Chrome: {e}")
            finally:
                self._temp_profile_dir = None
