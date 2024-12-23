from datetime import datetime
import re
import json
from src.database_manager import DatabaseManager
from src.utils import call_ollama, extract_categories, calculate_importance

class FamilyChatbot:
    def __init__(self, db_path='family_chatbot.db'):
        """Initialize the chatbot with a database connection."""
        self.db = DatabaseManager(db_path)
        
    def add_family_member(self, name, age, initial_info=None):
        """Add a new family member to track."""
        member_id = self.db.add_family_member(name, age, initial_info)
        if member_id:
            return f"Added {name} to the family circle!"
        else:
            return f"Failed to add {name}. They might already exist."

    def chat(self, name, message):
        """Main chat interface with improved context handling."""
        # Get member info first
        member_info = self.db.get_member_info(name)
        if not member_info:
            return f"Sorry, I don't know {name}. Please add them as a family member first."
        
        # Extract categories and importance
        categories = extract_categories(message)
        importance = calculate_importance(message)
        
        # Store in database
        self.db.store_memory(
            family_member_name=name,
            text=message,
            category=categories[0],  # Use primary category
            importance=importance
        )
        
        # Get relevant memories based on categories
        recent_memories = self.db.get_relevant_memories(name, categories, limit=2)
        
        # Build focused context
        context = self._build_context(name, member_info, recent_memories)
        
        # Generate and return response
        return self._generate_response(context, message)

    def _build_context(self, name, member_info, memories):
        """Build conversation context from member info and memories."""
        # Extract personal info
        personal_info = {}
        if member_info and member_info[3]:  # personal_info is at index 3
            try:
                personal_info = json.loads(member_info[3])
            except (json.JSONDecodeError, TypeError):
                personal_info = {}

        # Build initial context with member info
        context = f"You are chatting with {name}. "
        if personal_info:
            context += f"About them: {', '.join(f'{k}: {v}' for k, v in personal_info.items())}.\n\n"
        
        # Add categorized memories
        if memories:
            grouped_memories = {}
            for memory in memories:
                category = memory[4]  # category is at index 4
                if category not in grouped_memories:
                    grouped_memories[category] = []
                grouped_memories[category].append(memory[2])  # text is at index 2
            
            context += "Recent relevant conversations:\n"
            for category, msgs in grouped_memories.items():
                for msg in msgs:
                    context += f"- {msg}\n"
        
        return context

    def _generate_response(self, context, current_message):
        """Generate a focused response using Ollama."""
        prompt = f"""You are a friendly family chatbot assistant. Respond naturally to the current message while staying on topic.

Context:
{context}

Current message: {current_message}

Requirements for your response:
1. Stay focused on the current topic
2. Don't mention previous topics unless directly relevant
3. Keep responses concise and natural (1-2 sentences)
4. Don't add signatures or formalities
5. Respond as if you're having a casual conversation
6. Don't mention that you're a chatbot or AI
7. Don't offer reading suggestions unless specifically asked

Please provide a natural response:"""
        
        response = call_ollama(prompt)
        
        # Clean up response
        response = response.replace('Response:', '').strip()
        response = re.sub(r'\[.*?\]$', '', response).strip()  # Remove signatures
        response = re.sub(r'Best regards,.*$', '', response, flags=re.MULTILINE).strip()
        response = re.sub(r'Chatbot:', '', response, flags=re.MULTILINE).strip()
        
        return response

    def get_member_summary(self, name):
        """Get a summary of interactions with a family member."""
        # First check if member exists
        member_info = self.db.get_member_info(name)
        if not member_info:
            return f"No recorded interactions with {name} yet."
        
        # Get memory statistics
        stats = self.db.get_memory_stats(name)
        if not stats or stats[0] == 0:  # No memories or total_memories is 0
            return f"No recorded interactions with {name} yet."
            
        total_memories, avg_importance, latest = stats
        
        # Get category distribution
        categories = self.db.get_member_categories(name)
        
        # Build summary
        summary = f"Summary of interactions with {name}:\n"
        summary += f"Total memories: {total_memories}\n"
        
        if categories:
            summary += "Categories discussed:\n"
            for category, count in categories:
                summary += f"- {category}: {count} times\n"
        
        if latest:
            summary += f"Last interaction: {latest}\n"
            
        if avg_importance:
            summary += f"Average importance: {avg_importance:.2f}\n"
                
        return summary


    def update_member_info(self, name, new_info):
        """Update a family member's information."""
        success = self.db.update_member_info(name, new_info)
        if success:
            return f"Updated information for {name}"
        return f"Failed to update information for {name}"

    def cleanup_old_memories(self, days=30):
        """Clean up old memories."""
        self.db.delete_old_memories(days)
        return f"Cleaned up memories older than {days} days"
    
if __name__ == "__main__":
    # Simple test of the chatbot
    chatbot = FamilyChatbot()
    print("Testing chatbot...")
    
    # Add a family member
    print(chatbot.add_family_member("Alice", 35, {"role": "mother", "interests": ["reading", "gardening"]}))
    
    # Test chat
    test_messages = [
        "I spent the morning in my garden today!",
        "The roses are blooming beautifully.",
        "I'm thinking about adding some new flowers."
    ]
    
    for message in test_messages:
        print(f"\nUser (Alice): {message}")
        response = chatbot.chat("Alice", message)
        print(f"Chatbot: {response}")
        
    # Get member summary
    print("\nGetting member summary...")
    summary = chatbot.get_member_summary("Alice")
    print(summary)