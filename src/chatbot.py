from datetime import datetime
import re
import json
import re
from datetime import datetime
import random
from src.database_manager import DatabaseManager
from src.utils import call_ollama, extract_categories, calculate_importance




class FamilyChatbot:
    def __init__(self, db_path='family_chatbot.db'):
        """Initialize the chatbot with a database connection."""
        self.db = DatabaseManager(db_path)
        # Simple response templates for tiny LLM
        self.templates = {
            'greetings': [
                "G'day {}! How's things?",
                "Hey {}! Good to see ya!",
                "Welcome back {}! What's new?"
            ],
            'technical': [
                "Let's sort that {} issue. What's happening exactly?",
                "Right, tell me more about the {}.",
                "I can help with that {}. What have you tried so far?"
            ],
            'story': [
                "Here's a quick story: {}",
                "Let me tell you about {}",
                "Got a good one about {}"
            ],
            'generic': [
                "Tell me more about that!",
                "Sounds interesting, what happened next?",
                "That's fair dinkum! And then?"
            ]
        }

    def add_family_member(self, name, age, initial_info=None):
        """Add a new family member to track."""
        member_id = self.db.add_family_member(name, age, initial_info)
        if member_id:
            return f"Added {name} to the family circle!"
        return f"Failed to add {name}. They might already exist."

    def chat(self, name, message):
        """Main chat interface with simplified processing for tiny LLMs."""
        member_info = self.db.get_member_info(name)
        if not member_info:
            return f"Sorry, I don't know {name}. Please add them as a family member first."
        
        # Analyze message and get context
        msg_type = self._get_message_type(message)
        categories = self._get_categories(message)
        importance = self._calculate_importance(message)
        
        # Store interaction
        self.db.store_memory(
            family_member_name=name,
            text=message,
            category=categories[0],
            importance=importance
        )
        
        # Build minimal context
        context = self._build_minimal_context(name, member_info)
        
        # Generate response based on message type
        return self._generate_response(msg_type, context, message)

    def _get_message_type(self, message):
        """Determine basic message type for routing."""
        message = message.lower()
        if any(word in message for word in ['help', 'how', 'fix', 'repair', 'change']):
            return 'technical'
        elif any(word in message for word in ['story', 'tell me about']):
            return 'story'
        elif any(word in message for word in ['hi', 'hello', 'hey', "g'day"]):
            return 'greeting'
        return 'chat'

    def _get_categories(self, message):
        """Simple category matching for memory organization."""
        categories = {
            'technical': ['help', 'fix', 'repair', 'how to', 'problem'],
            'personal': ['feel', 'think', 'want', 'need'],
            'story': ['story', 'tell', 'share', 'happened'],
            'chat': ['chat', 'talk', 'discuss']
        }
        
        message = message.lower()
        matched = []
        for category, keywords in categories.items():
            if any(keyword in message for keyword in keywords):
                matched.append(category)
        return matched if matched else ['general']

    def _calculate_importance(self, message):
        """Simple importance calculation."""
        if any(word in message.lower() for word in ['urgent', 'emergency', 'help', 'serious']):
            return 0.8
        elif any(word in message.lower() for word in ['maybe', 'sometime', 'chat']):
            return 0.3
        return 0.5

    def _build_minimal_context(self, name, member_info):
        """Build minimal context string."""
        context = f"User: {name}"
        if member_info and member_info[3]:  # If personal_info exists
            try:
                info = json.loads(member_info[3])
                if info:
                    context += f", Info: {', '.join(f'{k}={v}' for k, v in info.items())}"
            except json.JSONDecodeError:
                pass
        return context

    def _generate_response(self, msg_type, context, message):
        """Generate response with better prompt handling for tiny LLMs."""
        # First determine if we need a joke, technical help, or general chat
        if "joke" in message.lower():
            prompt = """You're a friendly Aussie. Tell ONE short dad joke. Keep it clean and simple. Just the joke, no setup or extra text."""
        elif msg_type == 'technical':
            prompt = f"""You're a helpful Aussie mechanic. The user says: "{message}"
    Give ONE short, clear response asking what specific problem they're having.
    Just the response, no setup."""
        else:
            prompt = f"""You're a friendly Aussie. The user says: "{message}"
    Give ONE casual, friendly response.
    Just the response, no setup."""

        try:
            # Get response from model
            response = call_ollama(prompt)
            # Clean response thoroughly
            cleaned = self._clean_response(response)
            
            # If response is too short or got cleaned away, use template
            if len(cleaned) < 10:
                if "joke" in message.lower():
                    return "Why don't kangaroos tell jokes? Because they don't wanna get hopping mad!"
                elif msg_type == 'technical':
                    return "What seems to be the trouble with your bike, mate? Let's sort it out."
                else:
                    return random.choice(self.templates['generic'])
            
            return cleaned
            
        except Exception as e:
            print(f"Error generating response: {e}")
            return "G'day! Let's have a proper chat about that."

    def _clean_response(self, response):
        """Thoroughly clean model response."""
        if not response:
            return ""
            
        # Remove anything that looks like instructions or meta text
        response = re.sub(r'\[.*?\]', '', response)
        response = re.sub(r'\(.*?\)', '', response)
        response = re.sub(r'^.*?:', '', response)  # Remove any prefix with colon
        response = re.sub(r'Here\'s.*?:', '', response)  # Remove "Here's a..." prefixes
        response = re.sub(r'Sure.*?:', '', response)  # Remove "Sure, here's..." prefixes
        
        # Remove common prompt leakage patterns
        patterns_to_remove = [
            r'You\'re a friendly Aussie.*',
            r'As an AI.*',
            r'Let me.*:',
            r'I\'d be happy to.*:',
            r'Here\'s a response.*:',
            r'You asked for.*:',
            r'The user says.*:',
            r'Message:.*',
            r'Context:.*',
            r'User:.*',
            r'Reply:.*',
            r'Response:.*',
            r'Prompt:.*'
        ]
        
        for pattern in patterns_to_remove:
            response = re.sub(pattern, '', response, flags=re.IGNORECASE)
        
        # Clean up quotes and whitespace
        response = response.replace('"', '').replace('\'', '')
        response = ' '.join(response.split())
        
        # Remove any remaining system-style prefixes
        response = re.sub(r'^(System|Assistant|Chatbot|AI):', '', response)
        
        return response.strip()

    def get_member_summary(self, name):
        """Get basic summary of member interactions."""
        member_info = self.db.get_member_info(name)
        if not member_info:
            return f"No record found for {name}"
            
        stats = self.db.get_memory_stats(name)
        if not stats or stats[0] == 0:
            return f"No interactions recorded with {name}"
            
        total_memories, avg_importance, latest = stats
        return f"Summary for {name}: {total_memories} chats, last chat on {latest}"