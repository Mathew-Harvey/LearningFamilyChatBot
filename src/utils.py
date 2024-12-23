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
    """Extract potential categories from text."""
    categories = {
        'personal_info': ['name', 'age', 'birthday', 'address'],
        'preferences': ['like', 'love', 'hate', 'prefer', 'favorite'],
        'events': ['yesterday', 'today', 'tomorrow', 'last', 'next'],
        'relationships': ['family', 'friend', 'parent', 'child', 'sibling'],
        'daily_activities': ['usually', 'always', 'often', 'sometimes', 'daily']
    }
    
    text = text.lower()
    matched_categories = []
    
    for category, keywords in categories.items():
        if any(keyword in text for keyword in keywords):
            matched_categories.append(category)
    
    return matched_categories or ['general']

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