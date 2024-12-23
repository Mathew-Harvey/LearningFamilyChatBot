from src.chatbot import FamilyChatbot
import sys

def main():
    chatbot = FamilyChatbot('family_chatbot.db')
    
    print("Welcome to Family Chatbot! I'm a new member of your family.\n")
    print("You can use commands at any time:")
    print("  /add name age   - Add a new family member")
    print("  /switch name    - Switch to a different family member")
    print("  /quit           - Exit the chatbot")
    
    current_member = None
    
    while True:
        # If we don't have a current_member, ask who we're speaking with
        if not current_member:
            user_input = input("\nChatbot: Hi there, who am I speaking with?\nYou: ").strip()
            
            if user_input.lower() == '/quit':
                print("Chatbot: Goodbye!")
                break
            
            # Check if we already know this family member
            member_info = chatbot.db.get_member_info(user_input)
            if member_info:
                current_member = user_input
                print(f"Chatbot: Great to chat with you again, {current_member}!")
            else:
                # Offer to add them to the family
                answer = input(f"Chatbot: I don't think we've met. Would you like me to add you to the family? (yes/no)\nYou: ").strip().lower()
                if answer == 'yes':
                    try:
                        age = int(input("Chatbot: Awesome! How old are you?\nYou: ").strip())
                        result = chatbot.add_family_member(user_input, age, {})
                        print(f"Chatbot: {result}")
                        current_member = user_input
                    except ValueError:
                        print("Chatbot: Oops, that wasn't a valid age. Let's try again later.")
                else:
                    print("Chatbot: Okay, maybe another time then. Take care!")
                    break
        
        else:
            message = input(f"\n{current_member}: ").strip()
            
            if message.lower() == '/quit':
                print("Chatbot: Goodbye!")
                break
            
            elif message.startswith('/switch '):
                _, new_member = message.split(maxsplit=1)
                if chatbot.db.get_member_info(new_member):
                    current_member = new_member
                    print(f"Chatbot: Now chatting with {current_member}.")
                else:
                    print(f"Chatbot: I don't know {new_member} yet. Use /add name age to add them or pick someone else.")
            
            elif message.startswith('/add '):
                parts = message.split()
                if len(parts) < 3:
                    print("Chatbot: Usage: /add name age")
                else:
                    name, age_str = parts[1], parts[2]
                    try:
                        age = int(age_str)
                        add_result = chatbot.add_family_member(name, age, {})
                        print(f"Chatbot: {add_result}")
                    except ValueError:
                        print("Chatbot: Please provide a valid integer for age.")
            
            else:
                # Normal chat message
                response = chatbot.chat(current_member, message)
                print(f"Chatbot: {response}")

    chatbot.db.close_connection()

if __name__ == "__main__":
    main()