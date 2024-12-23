import requests
from datetime import datetime
import re

def call_ollama(prompt, model="tinyllama:chat"):
    """Make a call to the Ollama API."""
    try:
        response = requests.post('http://localhost:11434/api/generate',
            json={
                "model": model,
                "prompt": prompt,
                "stream": False
            })
        if response.status_code == 200:
            return response.json()['response']
        else:
            return f"Error: Received status code {response.status_code}"
    except requests.exceptions.RequestException as e:
        return f"Error connecting to Ollama: {str(e)}"

def extract_categories(text):
    """Enhanced category extraction with more nuanced detection."""
    categories = {
        'technical_help': ['help', 'how to', 'fix', 'repair', 'install', 'build', 'make'],
        'emotional_support': ['feel', 'sad', 'happy', 'worried', 'concerned', 'anxious'],
        'daily_life': ['today', 'went', 'doing', 'work', 'home', 'weekend'],
        'future_plans': ['planning', 'will', 'going to', 'future', 'next'],
        'preferences': ['like', 'love', 'hate', 'prefer', 'favorite'],
        'memories': ['remember', 'recalled', 'used to', 'past', 'when'],
        'advice_seeking': ['should', 'could', 'would', 'advice', 'suggest'],
        'general_chat': ['chat', 'talk', 'hello', 'hi', 'hey']
    }
    
    text = text.lower()
    matched_categories = []
    
    # Check for question markers
    if any(q in text for q in ['?', 'how', 'what', 'why', 'when', 'where', 'who']):
        matched_categories.append('question')
    
    # Match other categories
    for category, keywords in categories.items():
        if any(keyword in text for keyword in keywords):
            matched_categories.append(category)
    
    # Ensure we always return at least one category
    return matched_categories or ['general_chat']

def calculate_importance(text):
    """Calculate importance score based on content."""
    importance_markers = {
        'high': ['always', 'never', 'favorite', 'love', 'hate', 'important'],
        'medium': ['usually', 'often', 'like', 'dislike'],
        'low': ['sometimes', 'maybe', 'perhaps']
    }
    
    text = text.lower()
    
    if any(word in text for word in importance_markers['high']):
        return 0.8
    elif any(word in text for word in importance_markers['medium']):
        return 0.5
    elif any(word in text for word in importance_markers['low']):
        return 0.3
    
    return 0.4  # Default importance