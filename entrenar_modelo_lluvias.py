# -*- coding: utf-8 -*-
from pathlib import Path
import pandas as pd
from sklearn.linear_model import LinearRegression
import joblib

# Directorios base
BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "datos" / "datos_preparados_prohuerta.csv"
MODEL_DIR = BASE_DIR / "modelos"
MODEL_DIR.mkdir(exist_ok=True)

def entrenar_y_guardar_modelo_lluvias():
    if not DATA_PATH.exists():
        print(f"Error: No se encontró el archivo de datos en {DATA_PATH}")
        return

    # Cargamos el dataset preparado
    df = pd.read_csv(DATA_PATH)
    
    # Seleccionamos las variables predictoras (Precipitaciones y Oferta del Catálogo) y el objetivo (Cobertura)
    if "Precipitaciones_Hist_mm" not in df.columns or "Cobertura_Catalogo" not in df.columns:
        print("Error: Las columnas requeridas no están presentes en el dataset.")
        return

    X = df[['Precipitaciones_Hist_mm', 'Oferta_Catalogo']]
    y = df['Cobertura_Catalogo']
    
    # Entrenamos el modelo de regresión lineal
    modelo_lluvias = LinearRegression()
    modelo_lluvias.fit(X, y)
    
    # Guardamos el archivo joblib
    output_path = MODEL_DIR / "modelo_lluvias.joblib"
    joblib.dump(modelo_lluvias, output_path)
    print(f"¡Modelo de lluvias generado con éxito en: {output_path}!")

if __name__ == "__main__":
    entrenar_y_guardar_modelo_lluvias() 