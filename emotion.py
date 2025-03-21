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

def map_colors_to_valence_energy(colors):
  color_mapping = {
    "green": {"valence": 0.8, "energy": 0.5},
    "pink": {"valence": 0.9, "energy": 0.6},
    "black": {"valence": 0.2, "energy": 0.3},
    "red": {"valence": 0.7, "energy": 0.9},
    "yellow": {"valence": 1.0, "energy": 0.8},
    "cyan": {"valence": 0.8, "energy": 0.7},
    "brown": {"valence": 0.4, "energy": 0.3},
    "orange": {"valence": 0.9, "energy": 0.8},
    "white": {"valence": 0.9, "energy": 0.4},
    "purple": {"valence": 0.6, "energy": 0.5},
    "blue": {"valence": 0.7, "energy": 0.4},
    "grey": {"valence": 0.3, "energy": 0.2},
  }

  print("Calculating valence and energy...")

  valence_sum = 0
  energy_sum = 0
  cnt = 0

  for color in colors:
    tag = color["SimplifiedColor"]
    scores = color_mapping.get(tag)
    valence_sum += scores["valence"]
    energy_sum += scores["energy"]
    cnt += 1

  valence = valence_sum / cnt
  energy = energy_sum / cnt

  print("Valence: ", valence)
  print("Energy: ", energy)
  return (valence, energy)