import requests

def get_emotion_scores(text, api_key):
  """Get emotion scores using Hugging Face Inference API."""
  print("Getting emotion scores...")
  url = "https://api-inference.huggingface.co/models/j-hartmann/emotion-english-distilroberta-base"
  # Call inference API to classify text in Ekman's 6 basic emotions + neutral class
  headers = {"Authorization": f"Bearer {api_key}"}
  response = requests.post(url, headers=headers, json={"inputs": text})

  print("Received response from inference API")
  if response.status_code == 200:
    scores = response.json()[0]  # Get emotion predictions
    print(scores)
    return scores
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
  valence = sum(emotion['score'] * valence_mapping.get(emotion['label'], 0.5) for emotion in emotions)
  energy = sum(emotion['score'] * energy_mapping.get(emotion['label'], 0.5) for emotion in emotions)
  print("Valence: ", valence)
  print("Energy: ", energy)
    
  return round(valence, 2), round(energy, 2)