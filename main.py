import os
import sys
from utils.data_loader import load_and_validate_data    

# create directories if not exist
def setup_directories():

    directories = ['data', 'outputs/graphs', 'utils']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"Carpeta '{directory}' creada/verificada")

def main():
    print("Iniciando RPA")
    print("="*50)

    # setup directories
    setup_directories()

    # verify if file exists
    data_file = 'data/Ventas_Fundamentos.xlsx'

    if not os.path.exists(data_file):
        print(f"Archivo de datos no encontrado: {data_file}")
        print("Por favor, ejecute 'create_sample_data.py' para generar el archivo de datos de muestra.")
        sys.exit(1)
    
    # load and validate data
    print("Cargando y validando datos...")
    df, validation = load_and_validate_data(data_file)

    if df is not None and validation['is_valid']:
        print("Datos cargados y validados exitosamente.")
        print(f"Total registros: {len(df)}")
        print(f"Sedes: {df['Headquarter'].nunique()}")
        print(f"Modelos: {df['Model'].nunique()}")
        print(f'Clientes Únicos: {df["Client_ID"].nunique()}')
    else:
        print("Error en la carga de datos")
        if 'error' in validation:
            print(f"Error: {validation['error']}")
        sys.exit(1)

    print ("\n Módulo de datos completado correctamente.")
    # todo: analysis module

if __name__ == "__main__":
    main()