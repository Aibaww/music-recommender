import os
from configparser import ConfigParser
import requests

def get_emotion_scores(text):
  """Get emotion scores using Hugging Face Inference API."""
  # Get the API Key
  config_file = 'musicapp-config.ini'
  os.environ['AWS_SHARED_CREDENTIALS_FILE'] = config_file
    
  configur = ConfigParser()
  HUGGING_FACE_API_KEY = configur.get("hf","HUGGING_FACE_API_KEY")

  url = "https://api-inference.huggingface.co/models/j-hartmann/emotion-english-distilroberta-base"
  # Call inference API to classify text in Ekman's 6 basic emotions + neutral class
  headers = {"Authorization": f"Bearer {HUGGING_FACE_API_KEY}"}
  response = requests.post(url, headers=headers, json={"inputs": text})

  if response.status_code == 200:
    scores = response.json()[0]  # Get emotion predictions
    return {item["label"]: item["score"] for item in scores}
  else:
    print("Error:", response.json())
    return None

def map_emotions_to_valence_energy(emotions):
  """Map emotion scores to valence (happiness) and energy (activity)."""
  # Arbitrary mappings on a scale of 0 to 1
  valence_mapping = {
    "sadness": 0.1, "anger": 0.3, "disgust": 0.3,
    "fear": 0.2, "surprise": 0.7, "joy": 0.9, "neutral": 0.5
  }
  energy_mapping = {
    "sadness": 0.2, "anger": 0.8, "disgust": 0.4,
    "fear": 0.7, "surprise": 0.9, "joy": 0.8, "neutral": 0.5
  }

  # Translate all scores to valence & energy and get the sum
  valence = sum(emotions.get(emotion, 0) * valence_mapping.get(emotion, 0.5) for emotion in emotions)
  energy = sum(emotions.get(emotion, 0) * energy_mapping.get(emotion, 0.5) for emotion in emotions)
  print("Valence: ", valence)
  print("Energy: ", energy)
    
  return round(valence, 2), round(energy, 2)