import pandas as pd
import os
import logging

# config logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_excel_data(file_path: str, sheet_name= 0):

    try: 

        # verify that file exists

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Archivo no encontrado: {file_path}")
        
        # verify that is an excel file
        if not file_path.endswith(('.xlsx', '.xls')):
            raise ValueError("El archivo proporcionado no es un archivo de Excel válido.")
        
        logger.info(f"Cargando datos desde el archivo: {file_path}, hoja: {sheet_name}")
        
        # load excel file

        df = pd.read_excel(file_path, sheet_name=sheet_name)

        # basic validation

        if df.empty:
            logger.warning("El archivo de Excel está vacío.")
            return df
        
        logger.info(f"Datos cargados exitosamente")
        logger.info(f"Dimensiones: {df.shape[0]} filas y {df.shape[1]} columnas")
        logger.info(f"Columnas: {list(df.columns)}")

        # show basic info

        logger.info("\n" + "="*50)
        logger.info("Información del DataFrame:")
        logger.info("" + "="*50)
        logger.info(f"\n{df.info()}")
        logger.info(f"\nPrimeras 5 filas:\n{df.head()}")
        logger.info(f"\nEstadísticas descriptivas:\n{df.describe()}")

        return df
    
    except Exception as e:
        logger.error(f"Error al cargar el archivo de Excel: {e}")
        raise

# validate data structure

def validate_data_structure(df, required_columns= None):

    if required_columns is None:
        required_columns = ['Sell_Date', 'Headquarter', 'Model', 'Channel', 
                            'Segment', 'Client_ID', 'Price_Without_IGV', 
                            'IGV', 'Price_With_IGV']
       
    validation_result = {
        'is_valid': True,
        'missing_columns': [],
        'empty_data': False,
        'duplicate_rows': 0,
        'null_values': {}
    }

    #verify required columns

    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        validation_result['is_valid'] = False
        validation_result['missing_columns'] = missing_cols
        logger.error(f"Columnas faltantes: {missing_cols}")

    # verify if dataframe is empty

    if df.empty:
        validation_result['is_valid'] = False
        validation_result['empty_data'] = True
        logger.error("El DataFrame está vacío.")

    # count duplicate rows

    duplicates = df.duplicated().sum()
    validation_result['duplicate_rows'] = duplicates
    if duplicates > 0:
        validation_result['is_valid'] = False
        logger.warning(f"Número de filas duplicadas: {duplicates}")

    # verify null values in each column
    null_counts = df.isnull().sum()
    for col, null_count in null_counts.items():
        if null_count > 0:
            validation_result['is_valid'] = False
            validation_result['null_values'][col] = null_count
            logger.warning(f"Columna '{col}' tiene {null_count} valores nulos.")

    if validation_result['is_valid']:
        logger.info("El DataFrame ha pasado todas las validaciones.")
    else:
        logger.info("El DataFrame no ha pasado las validaciones.")

    return validation_result

# main load function

def load_and_validate_data(file_path):
    
    try:
        # 1. load excel data
        df = load_excel_data(file_path)
        # 2. validate data structure
        validation_report = validate_data_structure(df)
        # 3. return results
        return df, validation_report
    
    except Exception as e:
        logger.error(f"Error en la carga y validación de datos: {e}")
        return None, {'is_valid': False, 'error': str(e)}