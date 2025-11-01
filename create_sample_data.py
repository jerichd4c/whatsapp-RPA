import os
import pandas as pd
import random
from datetime import datetime, timedelta

def create_sample_data():

    # init config
    num_records = 100
    random.seed(42)

    # columns data

    headquarters = ['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix']
    models = ['Toyota Corolla', 'Honda Civic', 'Nissan Sentra', 'Hyundai Tucson', 
               'Kia Sportage', 'Mazda CX-5', 'Volkswagen Vento', 'Suzuki Swift',
               'Ford Escape', 'Chevrolet Onix']
    channels = ['Web', 'Ventas Directas', 'Concesionario', 'Telemarketing', 'Referido']
    segments = ['Individual', 'Corporativo', 'Empresarial', 'Gobierno']

    # generate unique IDs

    clients = [f'CLI_{i:05d}' for i in range(1,101)]

    # generate dates within the last year

    start_date = datetime.now() - timedelta(days=365)

    data = []

    for i in range(num_records):
        sell_date = start_date + timedelta(days=random.randint(0, 365))
        headquarter = random.choice(headquarters)
        model = random.choice(models)
        channel = random.choice(channels)   
        segment = random.choice(segments)
        client = random.choice(clients)

    # base price without IGV 
        price_without_igv = round(random.uniform(20000, 50000), 2)
        igv= round(price_without_igv * 0.18, 2) # IGV at 18%
        price_with_igv = round(price_without_igv + igv, 2)

        data.append({
            'Sell_Date': sell_date,
            'Headquarter': headquarter,
            'Model': model,
            'Channel': channel,
            'Segment': segment,
            'Client_ID': client,
            'Price_Without_IGV': price_without_igv,
            'IGV': igv,
            'Price_With_IGV': price_with_igv
        })

    # dataframe 

    df = pd.DataFrame(data)

    # ensure data directory exists and save to Excel
    os.makedirs('data', exist_ok=True)
    df.to_excel('data/Ventas_Fundamentos.xlsx', index=False)
    print("Archivo 'Ventas_Fundamentos.xlsx' creado exitosamente en la carpeta 'data'.")
    print(f"Total registros creados: {len(df)}")
    print(f"Headquarters: {df['Headquarter'].nunique()}")
    print(f"Models: {df['Model'].nunique()}")
    print(f'Unique Clients: {df["Client_ID"].nunique()}')

if __name__ == "__main__":
    create_sample_data()