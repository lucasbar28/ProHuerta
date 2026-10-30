import pandas as pd
from sklearn.linear_model import LinearRegression
import joblib
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "datos" / "preparados" / "solicitudes_v2.csv"
MODEL_PATH = BASE_DIR / "modelos" / "modelo_lluvias.joblib"

def reentrenar_modelo():
    print("Cargando datos...")
    df = pd.read_csv(DATA_PATH)
    
    # 1. Crear la variable climática según la regla de tu compañero
    def asignar_lluvia(temp):
        if temp == 'PV':
            return 650.0
        elif temp == 'OI':
            return 380.0
        return 500.0 # valor por defecto de seguridad
        
    df['Precipitaciones_Hist_mm'] = df['temporada'].apply(asignar_lluvia)
    
    # 2. Definir las columnas a usar
    feature_col = 'Precipitaciones_Hist_mm'
    target_col = 'cobertura_catalogo' 
    
    # Limpiar nulos
    df_clean = df.dropna(subset=[feature_col, target_col]).copy()
    
    X = df_clean[[feature_col]]
    y = df_clean[target_col]
    
    # Si la cobertura está guardada como fracción (ej: 0.8), la pasamos a % (80.0)
    if y.max() <= 1.0:
        y = y * 100.0
        
    print(f"Entrenando modelo honesto (solo con {feature_col})...")
    modelo_clima = LinearRegression()
    modelo_clima.fit(X, y)
    
    joblib.dump(modelo_clima, MODEL_PATH)
    print(f"¡Éxito! Nuevo modelo guardado en: {MODEL_PATH}")
    print(f"Coeficiente: {modelo_clima.coef_[0]:.4f} | Intercepto: {modelo_clima.intercept_:.4f}")

if __name__ == "__main__":
    reentrenar_modelo() 