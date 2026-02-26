import uuid
import random
import string
from faker import Faker

fake = Faker()

def random_string(length=8):
    return ''.join(random.choices(string.ascii_lowercase, k=length))

def generate_user_data():
    first = fake.first_name().lower()
    username = f"{first}{random.randint(10, 999)}"
    email = f"{username}@{random_string(6)}.com"
    
    return {
        "username": username,
        "email": email,
        "password": random_string(12),
    }

def generate_chat_message(min_words=3, max_words=15):
    """Generates a random sentence or short paragraph."""
    return fake.sentence(nb_words=random.randint(min_words, max_words))

def generate_chat_metadata():
    """Generates random metadata for a chat."""
    return {
        "title": fake.sentence(nb_words=4),
        "description": fake.paragraph(nb_sentences=2)
    }