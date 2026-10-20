import os
import joblib
import pandas as pd
from flask import Flask, render_template, request

app = Flask(__name__)

# Cargar los Pipelines entrenados
MODEL_REG_PATH = os.path.join('modelos', 'modelo_regresion.joblib')
MODEL_CLS_PATH = os.path.join('modelos', 'modelo_clasificacion.joblib')

modelo_regresion = joblib.load(MODEL_REG_PATH)
modelo_clasificacion = joblib.load(MODEL_CLS_PATH)

# Oferta oficial del catálogo por temporada/año
OFERTA_CATALOGO = {
    (2022, 'OI'): 7, (2023, 'OI'): 7,
    (2024, 'PV'): 9, (2025, 'OI'): 9, (2025, 'PV'): 12,
    (2026, 'OI'): 17, (2026, 'PV'): 18
}

@app.route('/', methods=['GET', 'POST'])
def index():
    prediccion_num = None
    alerta_regresion = None
    alerta_clasificador = None
    coinciden = None
    oferta_temporada = None
    
    if request.method == 'POST':
        # Captura de datos del formulario
        anio = int(request.form['anio'])
        temporada = request.form['temporada']
        tipo_localizacion = request.form['tipo_localizacion']
        tipo_huerta = request.form['tipo_huerta']
        experiencia = request.form['experiencia']
        superficie = request.form['superficie']
        destino = request.form['destino']
        ocupacion = request.form['ocupacion']
        
        # Determinar la oferta del catálogo
        oferta_temporada = OFERTA_CATALOGO.get((anio, temporada), 10)
        
        # Armar DataFrame de entrada para predict
        input_data = pd.DataFrame([{
            'Año': anio,
            'Temporada': temporada,
            'Tipo_Localizacion': tipo_localizacion,
            'Tipo_Huerta': tipo_huerta,
            'Experiencia_Huerta_Clean': experiencia,
            'Superficie_Clean': superficie,
            'Destino_Clean': destino,
            'Ocupacion_Clean': ocupacion,
            'Oferta_Catalogo': oferta_temporada
        }])
        
        # 1. Predicción Numérica (% Cobertura)
        pred_cobertura = float(modelo_regresion.predict(input_data)[0])
        pred_cobertura = max(0.0, min(100.0, pred_cobertura)) # Limitar entre 0 y 100%
        prediccion_num = round(pred_cobertura, 1)
        
        # 2. Alerta por Regresión + Umbral (>= 75%)
        alerta_regresion = 1 if pred_cobertura >= 75.0 else 0
        
        # 3. Alerta por Clasificador Directo
        alerta_clasificador = int(modelo_clasificacion.predict(input_data)[0])
        
        # 4. Verificar coincidencia
        coinciden = (alerta_regresion == alerta_clasificador)
        
    return render_template('index.html', 
                           prediccion_num=prediccion_num,
                           alerta_regresion=alerta_regresion,
                           alerta_clasificador=alerta_clasificador,
                           coinciden=coinciden,
                           oferta_temporada=oferta_temporada)

if __name__ == '__main__':
    app.run(debug=True)