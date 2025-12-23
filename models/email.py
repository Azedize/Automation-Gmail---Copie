"""
📧 Modèle de données Email
=====================================
Fournit une structure organisée pour gérer les emails
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

# Enum représentant les différents états possibles d'un email
class EmailStatus(Enum):
    PENDING = "pending"                  # En attente
    PROCESSING = "processing"            # En cours de traitement
    COMPLETED = "completed"              # Traitement terminé
    FAILED = "failed"                    # Échec
    BAD_PROXY = "bad_proxy"              # Proxy invalide
    ACCOUNT_CLOSED = "account_closed"    # Compte fermé
    PASSWORD_CHANGED = "password_changed"# Mot de passe changé
    SUSPICIOUS_ACTIVITY = "Activite_suspecte"  # Activité suspecte
    VALIDATION_REQUIRED = "code_de_validation" # Vérification requise
    CAPTCHA_REQUIRED = "validation_capcha"     # Captcha requis
    RECOVERY_CHANGED = "recoverychanged"       # Email de récupération modifié

# Dataclass pour configurer un proxy
@dataclass
class ProxyConfig:
    host: str                             # Adresse IP ou nom d'hôte du proxy
    port: str                             # Port du proxy
    username: Optional[str] = None        # Nom utilisateur (optionnel)
    password: Optional[str] = None        # Mot de passe (optionnel)

    @property
    def full_address(self) -> str:
        """Retourne l'adresse complète du proxy sans auth"""
        return f"{self.host}:{self.port}"

    @property
    def with_auth(self) -> str:
        """Retourne l'adresse du proxy avec authentification si disponible"""
        if self.username and self.password:
            return f"{self.username}:{self.password}@{self.host}:{self.port}"
        return self.full_address

    def to_dict(self) -> Dict[str, Any]:
        """Convertit le proxy en dictionnaire"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProxyConfig':
        """Crée un ProxyConfig à partir d'un dictionnaire"""
        return cls(**data)

# Dataclass représentant un email
@dataclass
class EmailData:
    email: str                            # Adresse email
    password: str                         # Mot de passe
    proxy: ProxyConfig                     # Configuration proxy
    recovery_email: Optional[str] = None   # Email de récupération actuel
    new_recovery_email: Optional[str] = None # Nouvel email de récupération
    new_password: Optional[str] = None     # Nouveau mot de passe
    status: EmailStatus = EmailStatus.PENDING # État de traitement
    error_message: Optional[str] = None    # Message d'erreur
    created_at: datetime = field(default_factory=datetime.now) # Date création
    updated_at: datetime = field(default_factory=datetime.now) # Date mise à jour
    metadata: Dict[str, Any] = field(default_factory=dict)     # Données supplémentaires

    def __post_init__(self):
        """Post-initialisation pour vérifier proxy et status"""
        if isinstance(self.proxy, dict):
            self.proxy = ProxyConfig(**self.proxy)
        if isinstance(self.status, str):
            try:
                self.status = EmailStatus(self.status)
            except ValueError:
                self.status = EmailStatus.PENDING

    @property
    def is_completed(self) -> bool:
        """Vérifie si l'email est complété"""
        return self.status == EmailStatus.COMPLETED

    @property
    def has_error(self) -> bool:
        """Vérifie si l'email a une erreur"""
        return self.status not in [EmailStatus.COMPLETED, EmailStatus.PROCESSING]

    def update_status(self, status: EmailStatus, error: Optional[str] = None):
        """Met à jour l'état de l'email et le message d'erreur"""
        self.status = status
        self.error_message = error
        self.updated_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'email en dictionnaire avec dates et status formatés"""
        data = asdict(self)
        data['status'] = self.status.value
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EmailData':
        """Crée un EmailData à partir d'un dictionnaire"""
        data = data.copy()
        if 'proxy' in data and isinstance(data['proxy'], dict):
            data['proxy'] = ProxyConfig(**data['proxy'])
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if 'updated_at' in data and isinstance(data['updated_at'], str):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        return cls(**data)

    @classmethod
    def from_raw_data(
        cls,
        email: str,
        password_email: str,
        ip_address: str,
        port: str,
        login: str = "",
        proxy_password: str = "",
        recovery_email: str = "",
        new_recovery_email: str = ""
    ) -> 'EmailData':
        """Crée un EmailData à partir de données brutes"""
        proxy = ProxyConfig(
            host=ip_address,
            port=port,
            username=login if login else None,
            password=proxy_password if proxy_password else None
        )
        return cls(
            email=email,
            password=password_email,
            proxy=proxy,
            recovery_email=recovery_email if recovery_email else None,
            new_recovery_email=new_recovery_email if new_recovery_email else None
        )

    def __str__(self) -> str:
        """Représentation simplifiée de l'email"""
        return f"EmailData(email={self.email}, status={self.status.value})"

    def __repr__(self) -> str:
        """Représentation détaillée pour debug"""
        return f"EmailData(email={self.email!r}, password=*****, proxy={self.proxy.full_address}, status={self.status.value})"

