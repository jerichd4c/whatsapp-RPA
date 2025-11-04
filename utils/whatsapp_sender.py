import os
import logging
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

logger = logging.getLogger(__name__)


class WhatsAppSender:

    # class for sending WhatsApp messages using Twilio API

    def __init__(self):

        # initialize sender

        self.config = self._load_config()
        self.twilio_client = None
        self._initialize_twilio_client()    

    def _load_config(self) -> Dict[str, Any]:

       # config loader

        # Read environment configuration. Normalize and strip whitespace.
        config = {
            'destination_whatsapp': (os.getenv('WHATSAPP_DESTINY') or os.getenv('DESTINATION_WHATSAPP') or '').strip(),
            # Twilio config
            'twilio_account_sid': os.getenv('TWILIO_ACCOUNT_SID', '').strip() or None,
            'twilio_auth_token': os.getenv('TWILIO_AUTH_TOKEN', '').strip() or None,
            'twilio_whatsapp_from': os.getenv('TWILIO_WHATSAPP_FROM', '').strip() or None,
            # Retry config
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
        
    # MAIN SEND METHOD (Twilio-only)

    def send_message(self, message: str, destiny: str = None, retry: bool = True, linked_file: Optional[List[str]] = None) -> bool:

        if not destiny:
            destiny = self.config['destination_whatsapp']

        if not destiny:
            logger.error("No se ha proporcionado un destino para el mensaje de WhatsApp.")
            return False

        max_retries = self.config['max_retries'] if retry else 1

        for attempt in range(max_retries):
            try:
                logger.info(f"Intentando envío via Twilio (intento {attempt + 1}/{max_retries})...")
                result = self.send_twilio_message(message, destiny, linked_file)
                if result:
                    return True
                logger.warning(f"Intento {attempt + 1} fallido.")
                if attempt < max_retries - 1:
                    time.sleep(self.config['wait_time'])
            except Exception as e:
                logger.error(f"Error en el intento {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(self.config['wait_time'])

        logger.error("Todos los intentos de envío via Twilio han fallado.")
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

            return success
        
        except Exception as e:
            logger.error(f"Error enviando reporte completo: {e}")
            return False
        
# aux function for direct use
def send_whatsapp_report(results: Dict[str, Any], destiny: str= None) -> bool:

    try:
        sender = WhatsAppSender()
        return sender.send_full_report(results, destiny)
    except Exception as e:
        logging.error(f"Error enviando reporte de WhatsApp: {e}")
        return False