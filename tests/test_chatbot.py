import sys
import os
import time
from pathlib import Path

# Add the project root directory to the Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.chatbot import FamilyChatbot

def cleanup_test_db(chatbot, test_db):
    """Helper function to properly cleanup test database."""
    try:
        if chatbot and chatbot.db:
            chatbot.db.close_connection()
        time.sleep(0.1)  # Allow time for connection to close
        if os.path.exists(test_db):
            try:
                os.remove(test_db)
            except PermissionError:
                print(f"Warning: Could not remove {test_db} - it may be in use")
    except Exception as e:
        print(f"Warning: Cleanup error - {str(e)}")

def test_add_family_member():
    """Test adding family members."""
    test_db = "test_family_chatbot.db"
    chatbot = None
    
    try:
        if os.path.exists(test_db):
            os.remove(test_db)
            
        chatbot = FamilyChatbot(test_db)
        
        # Test adding new member
        result = chatbot.add_family_member("Alice", 35, {"role": "mother", "interests": ["reading", "gardening"]})
        print("\nTest adding new member:")
        print(result)
        assert "Added Alice" in result
        
        # Test adding duplicate member
        result = chatbot.add_family_member("Alice", 35, {})
        print("\nTest adding duplicate member:")
        print(result)
        assert "Failed to add Alice" in result
        
    finally:
        cleanup_test_db(chatbot, test_db)

def test_chat_interactions():
    """Test chat functionality."""
    test_db = "test_family_chatbot.db"
    chatbot = None
    
    try:
        if os.path.exists(test_db):
            os.remove(test_db)
            
        chatbot = FamilyChatbot(test_db)
        
        # Add test member
        chatbot.add_family_member("Bob", 40, {"role": "father", "interests": ["sports", "cooking"]})
        
        # Test chat with non-existent member
        print("\nTest chat with non-existent member:")
        response = chatbot.chat("Alice", "Hello!")
        print(response)
        assert "don't know Alice" in response
        
        # Test normal chat interaction
        print("\nTest normal chat interaction:")
        messages = [
            "I made a great pasta dish today!",
            "Thinking of trying a new recipe tomorrow.",
            "The kids loved the dinner."
        ]
        
        for message in messages:
            print(f"\nUser (Bob): {message}")
            response = chatbot.chat("Bob", message)
            print(f"Chatbot: {response}")
            assert response and isinstance(response, str)
            
    finally:
        cleanup_test_db(chatbot, test_db)

def test_member_summary():
    """Test member summary functionality."""
    test_db = "test_family_chatbot.db"
    chatbot = None
    
    try:
        if os.path.exists(test_db):
            os.remove(test_db)
            
        chatbot = FamilyChatbot(test_db)
        
        # Test summary for non-existent member
        print("\nTest summary for non-existent member:")
        summary = chatbot.get_member_summary("Charlie")
        print(summary)
        assert "No recorded interactions with Charlie yet" in summary  # Updated assertion
        
        # Test summary for member with interactions
        chatbot.add_family_member("David", 45, {"role": "uncle", "interests": ["hiking", "photography"]})
        
        messages = [
            "Went on a great hike today!",
            "Captured some amazing sunset photos.",
            "Planning another hiking trip next week."
        ]
        
        for message in messages:
            chatbot.chat("David", message)
            
        print("\nTest summary for member with interactions:")
        summary = chatbot.get_member_summary("David")
        print(summary)
        assert "Total memories: 3" in summary
        
    finally:
        cleanup_test_db(chatbot, test_db)
        
def test_member_info_update():
    """Test updating member information."""
    test_db = "test_family_chatbot.db"
    chatbot = None
    
    try:
        if os.path.exists(test_db):
            os.remove(test_db)
            
        chatbot = FamilyChatbot(test_db)
        
        # Add test member
        chatbot.add_family_member("Eve", 28, {"role": "sister", "interests": ["music"]})
        
        # Update member info
        print("\nTest updating member info:")
        result = chatbot.update_member_info("Eve", {"role": "sister", "interests": ["music", "painting"]})
        print(result)
        assert "Updated information" in result
        
        # Verify update in chat context
        response = chatbot.chat("Eve", "I started painting yesterday!")
        print("\nTest updated context in chat:")
        print(f"Chatbot: {response}")
        
    finally:
        cleanup_test_db(chatbot, test_db)

def test_basic_interaction():
    """Run all basic interaction tests."""
    print("Starting Family Chatbot tests...\n")
    
    test_add_family_member()
    test_chat_interactions()
    test_member_summary()
    test_member_info_update()
    
    print("\nAll tests completed!")

if __name__ == "__main__":
    test_basic_interaction()