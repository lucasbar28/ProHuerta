import joblib
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "modelos" / "modelo_lluvias.joblib"

try:
    modelo_clima = joblib.load(MODEL_PATH)
except Exception as e:
    print(f"Advertencia: No se pudo cargar modelo_lluvias.joblib - {e}")
    modelo_clima = None

def estimar_cobertura_clima(precipitaciones: float) -> float:
    """
    Estima la cobertura (%) basada puramente en milímetros de precipitación.
    Se eliminó la dependencia de Oferta_Catalogo para evitar data leakage.
    """
    if modelo_clima is None:
        return 50.0  # Fallback seguro
        
    # El modelo ahora solo espera 1 feature
    X = pd.DataFrame([{"Precipitaciones_Hist_mm": precipitaciones}])
    
    pred = modelo_clima.predict(X)[0]
    
    # Recortamos entre 0 y 100% lógicamente
    return max(0.0, min(100.0, float(pred))) 