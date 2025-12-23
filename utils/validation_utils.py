import re
from typing import Tuple, Optional

class ValidationUtils:
    @staticmethod
    def validate_email(email: str) -> bool:
        """Valide une adresse email."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def parse_random_range(text: str) -> Tuple[int, int]:
        """Parse une plage aléatoire comme '50,100'."""
        if ',' in text:
            parts = text.split(',')
            if len(parts) == 2:
                return int(parts[0].strip()), int(parts[1].strip())
        return int(text), int(text)
    
    @staticmethod
    def generate_password(length: int = 16) -> str:
        """Génère un mot de passe sécurisé."""
        import random
        import string
        
        chars = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(random.choice(chars) for _ in range(length))