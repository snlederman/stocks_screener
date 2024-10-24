import requests
import pandas as pd
import time

# Tu clave API de Polygon.io
api_key = 'HLR3fNmkiaD8PwOavsZrX9yJtzr9uH82'

# Define el símbolo de la acción (ticker)
ticker = 'AAPL'

# Define la fecha inicial desde la que deseas comenzar a obtener datos (en formato AAAA-MM-DD)
start_date = '2022-01-01'

# Define la fecha final hasta la que deseas obtener datos (en formato AAAA-MM-DD)
end_date = '2022-12-31'

# URL base de la API de Polygon.io para datos intradiarios
base_url = 'https://api.polygon.io/v2/aggs/ticker/{}/range/1/minute/{}/{}?adjusted=true&sort=asc&limit=50000&apiKey={}'

# Inicializa un DataFrame vacío para almacenar todos los datos
all_data = pd.DataFrame()

# Bucle para obtener datos históricos de manera incremental por días
current_date = start_date
while current_date <= end_date:
    # Formatea la URL con el ticker y las fechas
    url = base_url.format(ticker, current_date, current_date, api_key)

    # Realiza la solicitud GET a la API
    response = requests.get(url)
    data = response.json()

    if 'results' in data:
        # Convierte los datos a un DataFrame de pandas
        day_data = pd.DataFrame(data['results'])

        # Convierte el timestamp a una fecha legible
        day_data['t'] = pd.to_datetime(day_data['t'], unit='ms')

        # Añade los datos del día al DataFrame completo
        all_data = pd.concat([all_data, day_data])

    # Incrementa la fecha actual en un día
    current_date = pd.to_datetime(current_date) + pd.DateOffset(days=1)
    current_date = current_date.strftime('%Y-%m-%d')

    # Espera un momento para evitar exceder el límite de la API
    time.sleep(1)  # Ajusta el tiempo según sea necesario

# Muestra los primeros y últimos registros de los datos obtenidos
print(all_data.head())
print(all_data.tail())
