import os
import sys

def config_whatsapp():

    print("CONFIGURACION DE WHATSAPP")
    print("="*40)

    # verify if config file exists
    if not os.path.exists("whatsapp_config.env"):
        print("Creando archivo whatsapp_config.env...")
        with open("whatsapp_config.env", "w") as f:
            f.write("# Configuracion inicial de WhatsApp\n")
        
    # read actual config

    config = {}
    if os.path.exists("whatsapp_config.env"):
        with open("whatsapp_config.env", "r") as f:
            for line in f:
                if "=" in line and not line.startswith("#"):
                    key, value = line.strip().split("=", 1)
                    config[key] = value

    # send method

    print("SELECCIONE EL METODO DE ENVIO DE MENSAJES:")
    print("1. Simulacion")
    print("2. Twilio API")
    print("3. Webhook personalizado")

    option = input("\nSelecciona opción (1-3) [1]: ").strip() or '1'

    if option == '1':
        config['WHATSAPP_METHOD'] = 'simulation'
    elif option == '2':
        config['WHATSAPP_METHOD'] = 'twilio'
        print("\nCONFIGURACION DE TWILIO API")
        config['TWILIO_ACCOUNT_SID'] = input("TWILIO_ACCOUNT_SID: ").strip()
        config['TWILIO_AUTH_TOKEN'] = input("TWILIO_AUTH_TOKEN: ").strip()
        config['TWILIO_WHATSAPP_FROM'] = input("TWILIO_WHATSAPP_FROM: ").strip()
    elif option == '3':
        config['WHATSAPP_METHOD'] = 'webhook'
        config['WHATSAPP_WEBHOOK_URL'] = input("URL del webhook: ").strip()
        config['WEBHOOK_TOKEN'] = input("Token de autenticación: ").strip()
    
    # destiny number

    destiny = input("\nNúmero destino: ").strip()
    if destiny:
        config['WHATSAPP_DESTINY'] = destiny

    # save config

    with open("whatsapp_config.env", "w") as f:
        f.write("# Configuracion de WhatsApp\n")
        for key, value in config.items():
            if value: # only write non-empty values
                f.write(f"{key}={value}\n")

    print("\nConfiguración guardada en whatsapp_config.env")
    print("INSTRUCCIONES:")
    if option == '1':
        print("Los mensajes se simularán y guardarán en outputs/whatsapp_simulado.txt")
    elif option == '2':
        print("Asegúrate de tener una cuenta activa en Twilio")
        print("Verifica que tu número de Twilio tenga habilitado WhatsApp")
    elif option == '3':
        print("Configura tu servidor para recibir las peticiones webhook")

    print("\nEjecuta 'python main.py' para probar el sistema")

if __name__ == "__main__":
    config_whatsapp()