import os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.utils import resample
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import joblib
from catboost import CatBoostClassifier
import urllib.request

def download_file_from_google_drive(id, destination):
    print(f"Downloading dataset to {destination}...")
    import requests
    URL = "https://docs.google.com/uc?export=download"
    session = requests.Session()
    response = session.get(URL, params = { 'id' : id }, stream = True)
    token = get_confirm_token(response)
    if token:
        params = { 'id' : id, 'confirm' : token }
        response = session.get(URL, params = params, stream = True)
    save_response_content(response, destination)
    print("Download complete.")

def get_confirm_token(response):
    for key, value in response.cookies.items():
        if key.startswith('download_warning'):
            return value
    return None

def save_response_content(response, destination):
    CHUNK_SIZE = 32768
    with open(destination, "wb") as f:
        for chunk in response.iter_content(CHUNK_SIZE):
            if chunk:
                f.write(chunk)

def main():
    os.makedirs('data', exist_ok=True)
    os.makedirs('models', exist_ok=True)
    
    dataset_path = 'data/post_data_without_timestamp.csv'
    file_id = '1-02Mcsp8tioC23htqZemiRpbv5I1RruK'
    
    if not os.path.exists(dataset_path):
        download_file_from_google_drive(file_id, dataset_path)
    
    print("Loading dataset...")
    df = pd.read_csv(dataset_path)
    
    # Drop missing values
    df = df.dropna()
    
    # One-hot encode categorical variables
    df = pd.get_dummies(df, drop_first=True)
    
    # Define target
    target = 'Feeling anxious_Yes'
    if target not in df.columns:
        raise ValueError(f"Target column '{target}' not found in the dataset.")
        
    # Separate features and target
    X = df.drop(columns=[target])
    y = df[target]
    
    # Balance the dataset using undersampling
    df_combined = pd.concat([X, y], axis=1)
    df_majority = df_combined[df_combined[target] == 1]
    df_minority = df_combined[df_combined[target] == 0]
    
    # Fixed missing 'df_majority_downsampled' from original script
    df_majority_downsampled = resample(df_majority, 
                                     replace=False,
                                     n_samples=len(df_minority),
                                     random_state=42)
                                     
    df_balanced = pd.concat([df_majority_downsampled, df_minority])
    df_balanced = df_balanced.sample(frac=1, random_state=42)
    
    # Split balanced data
    X_balanced = df_balanced.drop(columns=[target])
    y_balanced = df_balanced[target]
    
    X_train, X_test, y_train, y_test = train_test_split(X_balanced, y_balanced, test_size=0.4, random_state=47)
    
    print("Training CatBoost model...")
    # Train CatBoost model
    model = CatBoostClassifier(
        iterations=1000,
        depth=10,
        learning_rate=0.05,
        loss_function='Logloss',
        verbose=100
    )
    
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test)
    print("\nAccuracy:", accuracy_score(y_test, y_pred))
    print("Classification Report:\n", classification_report(y_test, y_pred))
    
    # Save model
    joblib.dump(model, 'models/catboostmodel_balanced.joblib')
    print("Model saved as 'models/catboostmodel_balanced.joblib'")

if __name__ == "__main__":
    main()
