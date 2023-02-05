import joblib
import json
import numpy as np
import os
from datetime import datetime

DATE_FORMAT = '%Y-%m-%dT%H:%M:%S.%f'
MODEL_ALGORITHM = 'light gradient boosting'
MODEL_NAME = 'insurance-model.pkl'

def init():
    global model
    # AZUREML_MODEL_DIR is an environment variable created during deployment.
    # It is the path to the model folder (./azureml-models/$MODEL_NAME/$VERSION)
    # For multiple models, it points to the folder containing all deployed models (./azureml-models)
    model_path = os.path.join(os.getenv('AZUREML_MODEL_DIR'), MODEL_NAME)
    # Deserialize the model file back into a sklearn model.
    model = joblib.load(model_path)

def run(data):
    '''
    data: is a input json that requests to API endpoint.
          data include: "data" list of float that request to API.
          for example:
            {'data': [[0,1,8,1,0,0,1,0,0,0,0,0,0,0,12,1,0,0,0.5,0.3,0.610327781,7,1,-1,0,-1,1,1,1,2,1,65,1,0.316227766,0.669556409,0.352136337,3.464101615,0.1,0.8,0.6,1,1,6,3,6,2,9,1,1,1,12,0,1,1,0,0,1],[4,2,5,1,0,0,0,0,1,0,0,0,0,0,5,1,0,0,0.9,0.5,0.771362431,4,1,-1,0,0,11,1,1,0,1,103,1,0.316227766,0.60632002,0.358329457,2.828427125,0.4,0.5,0.4,3,3,8,4,10,2,7,2,0,3,10,0,0,1,1,0,1]]}
    '''
    try:
        start_time = datetime.strftime(datetime.now(), DATE_FORMAT)
        test = json.loads(data)
        input_data = test['data']
        np_data = np.array(input_data)
        score = model.predict(np_data).tolist()
        end_time = datetime.strftime(datetime.now(), DATE_FORMAT)
        # You can return any JSON-serializable object.
        result = {
                'model_algorithm': MODEL_ALGORITHM,
                'local_feature_importances': None,
                'prediction_score': score,
                'start_time': start_time,
                'end_time': end_time
            }
        return json.dumps(result)

    except Exception as e:
        error = str(e)
        return error