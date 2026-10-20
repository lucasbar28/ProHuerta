import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.tree import DecisionTreeRegressor, DecisionTreeClassifier

# 1. Cargar dataset preparado
df = pd.read_csv('datos/datos_preparados_prohuerta.csv')

predictors = ['Año', 'Temporada', 'Tipo_Localizacion', 'Tipo_Huerta', 'Experiencia_Huerta_Clean', 
              'Superficie_Clean', 'Destino_Clean', 'Ocupacion_Clean', 'Oferta_Catalogo']

X = df[predictors]
y_reg = df['Cobertura_Catalogo']
y_cls = df['Alerta_Alta_Demanda']

# 2. Partición de datos
df['strat_col'] = df['Temporada'].astype(str) + "_" + df['Alerta_Alta_Demanda'].astype(str)

X_train, X_temp, y_reg_train, y_reg_temp, y_cls_train, y_cls_temp = train_test_split(
    X, y_reg, y_cls, test_size=0.40, random_state=42, stratify=df['strat_col']
)

# 3. Preprocesador
cat_cols = ['Temporada', 'Tipo_Localizacion', 'Tipo_Huerta', 'Experiencia_Huerta_Clean', 
            'Superficie_Clean', 'Destino_Clean', 'Ocupacion_Clean']
num_cols = ['Año', 'Oferta_Catalogo']

preprocessor = ColumnTransformer(
    transformers=[
        ('num', StandardScaler(), num_cols),
        ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), cat_cols)
    ]
)

# 4. Entrenar Regresión
pipeline_reg = Pipeline([
    ('prep', preprocessor),
    ('model', DecisionTreeRegressor(max_depth=4, random_state=42))
])
pipeline_reg.fit(X_train, y_reg_train)

# 5. Entrenar Clasificación
pipeline_cls = Pipeline([
    ('prep', preprocessor),
    ('model', DecisionTreeClassifier(max_depth=5, random_state=42))
])
pipeline_cls.fit(X_train, y_cls_train)

# 6. Guardar los archivos en la carpeta modelos/
joblib.dump(pipeline_reg, 'modelos/modelo_regresion.joblib')
joblib.dump(pipeline_cls, 'modelos/modelo_clasificacion.joblib')

print("✅ ¡Modelos guardados con éxito en la carpeta modelos/!")