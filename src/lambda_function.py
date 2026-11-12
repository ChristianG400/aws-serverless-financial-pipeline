import json
import urllib.parse
import boto3
import awswrangler as wr
import pandas as pd

s3 = boto3.client('s3')

def lambda_handler(event, context):
    try:
        # 1. Capturar el evento automático de S3
        bucket_origen = event['Records'][0]['s3']['bucket']['name']
        archivo_clave = urllib.parse.unquote(event['Records'][0]['s3']['object']['key'])
        
        # Nombre de salida dinámico corregido
        bucket_destino = "finanzas-reportes-limpios-cristian-097"
        nombre_salida_parquet = archivo_clave.replace('.csv', '.parquet')
        path_destino = f"s3://{bucket_destino}/{nombre_salida_parquet}"
        
        print(f"Procesando archivo: {archivo_clave} desde el bucket: {bucket_origen}")

        # 2. Leer el archivo CSV directo de S3 a un DataFrame de Pandas
        path_origen = f"s3://{bucket_origen}/{archivo_clave}"
        df = wr.s3.read_csv(path=path_origen)

        # 3. LÓGICA DE LIMPIEZA (ETL)
        df.dropna(how='all', inplace=True)
        df.drop_duplicates(subset=['id_transaccion'], keep='first', inplace=True)
        df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce').dt.strftime('%Y-%m-%d')
        df['monto'] = pd.to_numeric(df['monto'], errors='coerce')

        # 4. Convertir a Parquet y escribir en el S3 de destino
        wr.s3.to_parquet(df=df, path=path_destino, dataset=False)
        
        return {
            'statusCode': 200,
            'body': json.dumps('Procesamiento ETL completado exitosamente.')
        }
    except Exception as e:
        print(f"Error procesando el pipeline: {str(e)}")
        raise e