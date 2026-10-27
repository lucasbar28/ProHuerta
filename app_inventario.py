# -*- coding: utf-8 -*-
from pathlib import Path
import joblib
import pandas as pd
from flask import Flask, render_template, request, jsonify

BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR / "modelos"

# Cargamos los modelos originales (asegúrate de que los nombres de los archivos correspondan)
MODEL_REG_PATH = MODEL_DIR / "modelo_regresion_cobertura.joblib" 
MODEL_CLS_PATH = MODEL_DIR / "modelo_clasificacion.joblib"

modelo_regresion = joblib.load(MODEL_REG_PATH)
modelo_clasificacion = joblib.load(MODEL_CLS_PATH)

app = Flask(__name__)

# Oferta oficial del catálogo por temporada/año
OFERTA_CATALOGO = {
    (2022, 'OI'): 7, (2023, 'OI'): 7,
    (2024, 'PV'): 9, (2025, 'OI'): 9, (2025, 'PV'): 12,
    (2026, 'OI'): 17, (2026, 'PV'): 18
}

@app.route('/', methods=['GET', 'POST'])
def index():
    contexto = {
        "prediccion_num": None,
        "alerta_regresion": None,
        "alerta_clasificador": None,
        "coinciden": None,
        "oferta_temporada": None
    }
    
    if request.method == 'POST':
        try:
            anio = int(request.form.get('anio', 2026))
            temporada = request.form.get('temporada', 'PV').upper()
            
            contexto["oferta_temporada"] = OFERTA_CATALOGO.get((anio, temporada), 10)
            
            input_data = pd.DataFrame([{
                'Año': anio,
                'Temporada': temporada,
                'Tipo_Localizacion': request.form.get('tipo_localizacion', 'urbana'),
                'Tipo_Huerta': request.form.get('tipo_huerta', 'familiar'),
                'Experiencia_Huerta_Clean': request.form.get('experiencia', 'primera vez'),
                'Superficie_Clean': request.form.get('superficie', 'hasta 5 m2'),
                'Destino_Clean': request.form.get('destino', 'autoconsumo'),
                'Ocupacion_Clean': request.form.get('ocupacion', 'empleado/a'),
                'Oferta_Catalogo': contexto["oferta_temporada"]
            }])
            
            # 1. Predicción Numérica (% Cobertura)
            pred_cobertura = float(modelo_regresion.predict(input_data)[0])
            pred_cobertura = max(0.0, min(100.0, pred_cobertura))
            contexto["prediccion_num"] = round(pred_cobertura, 1)
            
            # 2. Alerta por Regresión + Umbral (>= 75%)
            contexto["alerta_regresion"] = 1 if pred_cobertura >= 75.0 else 0
            
            # 3. Alerta por Clasificador Directo
            contexto["alerta_clasificador"] = int(modelo_clasificacion.predict(input_data)[0])
            
            # 4. Verificar coincidencia
            contexto["coinciden"] = (contexto["alerta_regresion"] == contexto["alerta_clasificador"])
            
        except Exception as e:
            return jsonify({"error": str(e)}), 400
            
    return render_template('index.html', **contexto)

if __name__ == '__main__':
    # Ejecutamos en un puerto distinto para que puedas correr ambos simultáneamente
    app.run(debug=True, port=5001) 