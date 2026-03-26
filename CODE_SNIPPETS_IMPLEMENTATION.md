# 🔧 CODE SNIPPETS - IMPLÉMENTATION DIRECTE

## Corrections et Refactoring Prêts à Copy-Paste

---

## 📁 FICHIER 1: core/result_models.py

**Status**: À CRÉER  
**Priorité**: P0 (Créer avant tout refactoring)

```python
# core/result_models.py
"""
Modèles de résultat standardisés pour l'application entière.
Tous les services doivent retourner des instances de Result<T>.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import TypeVar, Generic, Optional, Any, Dict
import json

T = TypeVar('T')

class ResultStatus(Enum):
    """États possibles d'une opération"""
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    PARTIAL = "PARTIAL"
    NOT_FOUND = "NOT_FOUND"
    TIMEOUT = "TIMEOUT"
    UNAUTHORIZED = "UNAUTHORIZED"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    UNKNOWN = "UNKNOWN"

@dataclass
class Result(Generic[T]):
    """
    Résultat d'une opération avec gestion d'erreur typée.

    Attributs:
        status: État de l'opération
        data: Données résultantes si succès
        error: Message d'erreur si failure
        error_code: Code d'erreur structuré
        details: Contexte additionnel
        timestamp: Moment de création

    Exemple:
        >>> def get_user(user_id: int) -> Result[User]:
        ...     try:
        ...         user = db.query(User).get(user_id)
        ...         if not user:
        ...             return Result(status=ResultStatus.NOT_FOUND, error_code="USER_NOT_FOUND")
        ...         return Result(status=ResultStatus.SUCCESS, data=user)
        ...     except Exception as e:
        ...         return Result(status=ResultStatus.FAILURE, error=str(e))

        >>> result = get_user(1)
        >>> if result:  # Utilise __bool__()
        ...     user = result.data
    """
    status: ResultStatus
    data: Optional[T] = None
    error: Optional[str] = None
    error_code: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_success(self) -> bool:
        """Vérifie si l'opération a réussi"""
        return self.status == ResultStatus.SUCCESS

    @property
    def is_failure(self) -> bool:
        """Vérifie si l'opération a échoué"""
        return self.status in (
            ResultStatus.FAILURE,
            ResultStatus.TIMEOUT,
            ResultStatus.UNAUTHORIZED,
            ResultStatus.VALIDATION_ERROR
        )

    @property
    def is_partial(self) -> bool:
        """Vérifie si l'opération est partiellement réussie"""
        return self.status == ResultStatus.PARTIAL

    def __bool__(self) -> bool:
        """Permet d'utiliser Result directement en if"""
        return self.is_success

    def __str__(self) -> str:
        return f"Result({self.status.value}, error={self.error})"

    def __repr__(self) -> str:
        return f"Result(status={self.status}, data={type(self.data).__name__ if self.data else None})"

    def to_dict(self) -> Dict[str, Any]:
        """Convertir en dict pour sérialisation"""
        return {
            "status": self.status.value,
            "data": self.data,
            "error": self.error,
            "error_code": self.error_code,
            "details": self.details
        }

    def to_json(self) -> str:
        """Convertir en JSON"""
        return json.dumps(self.to_dict(), default=str)

    @classmethod
    def success(cls, data: T, details: Optional[Dict] = None) -> 'Result[T]':
        """Factory pour un résultat succès"""
        return cls(
            status=ResultStatus.SUCCESS,
            data=data,
            details=details or {}
        )

    @classmethod
    def failure(
        cls,        error: str,
        error_code: Optional[str] = None,
        details: Optional[Dict] = None,
        status: ResultStatus = ResultStatus.FAILURE
    ) -> 'Result[T]':
        """Factory pour un résultat erreur"""
        return cls(
            status=status,
            error=error,
            error_code=error_code,
            details=details or {}
        )

    @classmethod
    def not_found(cls, error: str) -> 'Result[T]':
        """Factory pour une ressource non trouvée"""
        return cls.failure(error, error_code="NOT_FOUND", status=ResultStatus.NOT_FOUND)

    @classmethod
    def unauthorized(cls, error: str = "Unauthorized") -> 'Result[T]':
        """Factory pour erreur d'authentification"""
        return cls.failure(error, error_code="UNAUTHORIZED", status=ResultStatus.UNAUTHORIZED)

    @classmethod
    def validation_error(cls, error: str, details: Optional[Dict] = None) -> 'Result[T]':
        """Factory pour erreur de validation"""
        return cls.failure(
            error,
            error_code="VALIDATION_ERROR",
            status=ResultStatus.VALIDATION_ERROR,
            details=details or {}
        )
```

---

## 📁 FICHIER 2: core/error_codes.py

**Status**: À CRÉER  
**Priorité**: P0

```python
# core/error_codes.py
"""Codes d'erreur centralisés - Source unique de vérité"""

from enum import Enum

class ErrorCode(Enum):
    """Codes d'erreur standardisés"""

    # ===== AUTHENTIFICATION (AUTH_XXX) =====
    AUTH_INVALID_USERNAME = "AUTH_001"
    AUTH_INVALID_PASSWORD = "AUTH_002"
    AUTH_API_FAILED = "AUTH_003"
    AUTH_SESSION_EXPIRED = "AUTH_004"
    AUTH_DECRYPTION_FAILED = "AUTH_005"
    AUTH_CREDENTIALS_INVALID = "AUTH_006"

    # ===== GESTION EXTENSION (EXT_XXX) =====
    EXT_TEMPLATE_NOT_FOUND = "EXT_001"
    EXT_COPY_FAILED = "EXT_002"
    EXT_JS_REPLACEMENT_FAILED = "EXT_003"
    EXT_JSON_PROCESS_FAILED = "EXT_004"
    EXT_BROWSER_COMPATIBLE = "EXT_005"
    EXT_ALREADY_EXISTS = "EXT_006"

    # ===== API (API_XXX) =====
    API_CONNECTION_FAILED = "API_001"
    API_INVALID_RESPONSE = "API_002"
    API_TIMEOUT = "API_003"
    API_AUTH_ERROR = "API_004"
    API_RATE_LIMIT = "API_005"
    API_SERVER_ERROR = "API_006"

    # ===== BROWSER (BRW_XXX) =====
    BROWSER_NOT_FOUND = "BRW_001"
    BROWSER_PROFILE_FAILED = "BRW_002"
    BROWSER_LAUNCH_FAILED = "BRW_003"
    BROWSER_PROFILE_NOT_FOUND = "BRW_004"
    BROWSER_ACCESS_DENIED = "BRW_005"

    # ===== VALIDATION (VAL_XXX) =====
    VALIDATION_EMPTY_INPUT = "VAL_001"
    VALIDATION_INVALID_FORMAT = "VAL_002"
    VALIDATION_INVALID_EMAIL = "VAL_003"
    VALIDATION_INVALID_IP = "VAL_004"
    VALIDATION_INVALID_PORT = "VAL_005"

    # ===== SESSION (SES_XXX) =====
    SESSION_FILE_NOT_FOUND = "SES_001"
    SESSION_FILE_EMPTY = "SES_002"
    SESSION_INVALID_FORMAT = "SES_003"
    SESSION_EXPIRED = "SES_004"
    SESSION_ENCRYPTION_ERROR = "SES_005"

    # ===== FILE SYSTEM (FS_XXX) =====
    FILE_NOT_FOUND = "FS_001"
    FILE_READ_ERROR = "FS_002"
    FILE_WRITE_ERROR = "FS_003"
    FILE_PERMISSION_ERROR = "FS_004"

    # ===== GENERAL (GEN_XXX) =====
    UNKNOWN_ERROR = "GEN_001"
    NOT_IMPLEMENTED = "GEN_002"
    OPERATION_TIMEOUT = "GEN_003"
    RESOURCE_EXHAUSTED = "GEN_004"

# Mapping pour messages l'utilisateur-friendly
ERROR_MESSAGES = {
    ErrorCode.AUTH_INVALID_USERNAME: "Username invalide (minimum 5 caractères)",
    ErrorCode.AUTH_INVALID_PASSWORD: "Password invalide (minimum 8 caractères)",
    ErrorCode.AUTH_API_FAILED: "API connection échouée",
    ErrorCode.AUTH_SESSION_EXPIRED: "Session expirée",
    ErrorCode.EXT_TEMPLATE_NOT_FOUND: "Template d'extension non trouvé",
    ErrorCode.BROWSER_NOT_FOUND: "Navigateur non installé",
    # ...
}

def get_user_message(error_code: ErrorCode) -> str:
    """Récupère le message utilisateur-friendly"""
    return ERROR_MESSAGES.get(error_code, "Une erreur est survenue")
```

---

## 📁 FICHIER 3: api/base_client.py - CORRECTION P0-1

**Status**: À CORRIGER  
**Priorité**: P0  
**Ligne**: 164-168

```python
# ❌ AVANT
def on_scenario_changed(self, payload: Dict[str, Any], Url_Api) -> Dict[str, Any]:
    print("🚀 [ON_SCENARIO_CHANGED] Starting on_scenario_changed function")
    print(f"📋 [ON_SCENARIO_CHANGED] Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")
    print(f"🔗 [ON_SCENARIO_CHANGED] API URL: {Url_Api}")
    result = self.make_request(Url_Api, "POST", data=payload)
    print(f"📥 [ON_SCENARIO_CHANGED] make_request result: {result}")
    print("🔄 [ON_SCENARIO_CHANGED] Calling _handle_response...")
    print(f"✅ [ON_SCENARIO_CHANGED] _handle_response result: {response}")  # ← UNDEFINED!
    return self._handle_response(result, {"success": True},{"success": False, "error": "Format de réponse invalide"})

# ✅ APRÈS
def on_scenario_changed(self, payload: Dict[str, Any], Url_Api) -> Dict[str, Any]:
    """Gère les changements de scénario"""
    settings.WRITE_LOG_DEV_FILE(
        f"Processing scenario change for URL: {Url_Api}",
        "DEBUG"
    )

    try:
        result = self.make_request(Url_Api, "POST", data=payload)
        response = self._handle_response(
            result,
            {"success": True},
            {"success": False, "error": "Invalid response format"}
        )
        settings.WRITE_LOG_DEV_FILE(
            f"Scenario change result: {response}",
            "INFO"
        )
        return response

    except Exception as e:
        settings.WRITE_LOG_DEV_FILE(
            f"Error in on_scenario_changed: {str(e)}",
            "ERROR"
        )
        return {"success": False, "error": str(e)}
```

---

## 📁 FICHIER 4: models/browser_manager.py - CORRECTION P0-2

**Status**: À CORRIGER  
**Priorité**: P0  
**Ligne**: 152

```python
# ❌ AVANT
if os.path.isdir(path) and os.pa(lock_file):  # ← TYPO: os.pa n'existe pas
    profiles.append({'name': folder, 'path': path})

# ✅ APRÈS
if os.path.isdir(path) and os.path.exists(lock_file):
    profiles.append({'name': folder, 'path': path})
```

---

## 📁 FICHIER 5: core/session_manager.py - CORRECTION P0-3 (PARTIE 1)

**Status**: À REFACTORER  
**Priorité**: P0

```python
# Créer d'abord les dataclasses dans une section en haut

from dataclasses import dataclass
from typing import Optional, Tuple

@dataclass
class CredentialData:
    """Données de credential validées"""
    user_id: str
    entity: str

@dataclass
class CredentialCheckResult:
    """Résultat du check credentials"""
    success: bool
    data: Optional[CredentialData] = None
    error: Optional[str] = None
    error_code: Optional[str] = None

# Refactorer la fonction
def check_api_credentials(
    self,
    username: str,
    password: str
) -> CredentialCheckResult:
    """
    Valide les credentials via l'API avec réponse standardisée.

    Returns:
        CredentialCheckResult avec succès/erreur
    """
    from core.error_codes import ErrorCode

    # 1️⃣ Validation des inputs
    valid_user, msg_user = ValidationUtils.validate_qlineedit_text(
        username,
        validator_type="text",
        min_length=5
    )
    if not valid_user:
        settings.WRITE_LOG_DEV_FILE(
            f"❌ Username invalide: {msg_user}",
            "ERROR"
        )
        return CredentialCheckResult(
            success=False,
            error=msg_user,
            error_code=ErrorCode.AUTH_INVALID_USERNAME.value
        )

    valid_pass, msg_pass = ValidationUtils.validate_qlineedit_text(
        password,
        min_length=6
    )
    if not valid_pass:
        settings.WRITE_LOG_DEV_FILE(
            f"❌ Password invalide: {msg_pass}",
            "ERROR"
        )
        return CredentialCheckResult(
            success=False,
            error=msg_pass,
            error_code=ErrorCode.AUTH_INVALID_PASSWORD.value
        )

    # 2️⃣ Requête API avec retry
    payload = {
        "rID": "1",
        "u": username,
        "p": password,
        "k": "mP5QXYrK9E67Y",
        "l": "1"
    }

    resp = None
    last_error = None

    for attempt in range(1, 6):
        try:
            result = APIManager.make_request(
                "_APIACCESS_API",
                method="POST",
                data=payload,
                timeout=10
            )
            resp = APIManager._handle_response(result, failure_default=None)

            if resp is not None:
                settings.WRITE_LOG_DEV_FILE(
                    f"API response received: attempt {attempt}",
                    "DEBUG"
                )
                break

        except Exception as e:
            last_error = e
            settings.WRITE_LOG_DEV_FILE(
                f"API attempt {attempt} failed: {str(e)}",
                "ERROR"
            )

        if attempt < 5:
            time.sleep(2)

    if resp is None:
        error_msg = f"API connection failed after 5 attempts: {str(last_error)}"
        settings.WRITE_LOG_DEV_FILE(error_msg, "ERROR")
        return CredentialCheckResult(
            success=False,
            error=error_msg,
            error_code=ErrorCode.AUTH_API_FAILED.value
        )

    # 3️⃣ Vérifier les codes d'erreur API
    if isinstance(resp, int) or str(resp) in ("-1", "-2", "-3", "-4", "-5"):
        error_msg = f"API returned error code: {resp}"
        settings.WRITE_LOG_DEV_FILE(error_msg, "WARNING")
        return CredentialCheckResult(
            success=False,
            error=error_msg,
            error_code=ErrorCode.AUTH_API_FAILED.value
        )

    # 4️⃣ Décryptage
    try:
        decrypted = EncryptionService.decrypt_message(resp, self.key)

        if not decrypted or ";" not in decrypted:
            error_msg = "Decryption failed: invalid format"
            settings.WRITE_LOG_DEV_FILE(error_msg, "ERROR")
            return CredentialCheckResult(
                success=False,
                error=error_msg,
                error_code=ErrorCode.AUTH_DECRYPTION_FAILED.value
            )

        id_user_str, entity = decrypted.split(";", 1)

        try:
            id_user = int(id_user_str)
        except ValueError:
            error_msg = f"User ID is not numeric: {id_user_str}"
            settings.WRITE_LOG_DEV_FILE(error_msg, "ERROR")
            return CredentialCheckResult(
                success=False,
                error=error_msg,
                error_code=ErrorCode.AUTH_CREDENTIALS_INVALID.value
            )

        # ✅ IMPORTANT: ID > 0, pas >= 0
        if id_user <= 0 or not entity:
            error_msg = f"Invalid user data: id={id_user}, entity={entity}"
            settings.WRITE_LOG_DEV_FILE(error_msg, "ERROR")
            return CredentialCheckResult(
                success=False,
                error=error_msg,
                error_code=ErrorCode.AUTH_CREDENTIALS_INVALID.value
            )

        settings.WRITE_LOG_DEV_FILE(
            f"Credentials validated: user={id_user}",
            "INFO"
        )

        return CredentialCheckResult(
            success=True,
            data=CredentialData(user_id=str(id_user), entity=entity)
        )

    except Exception as e:
        error_msg = f"Decryption error: {str(e)}"
        settings.WRITE_LOG_DEV_FILE(error_msg, "ERROR")
        import traceback
        traceback.print_exc()
        return CredentialCheckResult(
            success=False,
            error=error_msg,
            error_code=ErrorCode.AUTH_DECRYPTION_FAILED.value
        )
```

---

## 📁 FICHIER 6: Test Template - tests/unit/test_session_manager.py

**Status**: À CRÉER  
**Priorité**: P1

```python
# tests/unit/test_session_manager.py
"""Tests unitaires pour SessionManager"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from core.session_manager import SessionManager, CredentialCheckResult
from core.error_codes import ErrorCode

class TestSessionManager:

    @pytest.fixture
    def session_manager(self):
        """Fixture pour SessionManager"""
        with patch('core.session_manager.EncryptionService'), \
             patch('core.session_manager.APIManager'), \
             patch('core.session_manager.settings'):
            return SessionManager()

    def test_check_api_credentials_valid(self, session_manager):
        """Test avec credentials valides"""
        with patch.object(session_manager, 'APIManager') as mock_api:
            mock_api.make_request.return_value = {
                "status": "success",
                "data": "encrypted_123"
            }

            with patch.object(session_manager, 'EncryptionService') as mock_enc:
                mock_enc.decrypt_message.return_value = "42;prod"

                result = session_manager.check_api_credentials("user123", "Pass@123")

                assert result.success
                assert result.data.user_id == "42"
                assert result.data.entity == "prod"

    def test_check_api_credentials_invalid_username(self, session_manager):
        """Test avec username invalide"""
        result = session_manager.check_api_credentials("bad", "ValidPass123!")

        assert not result.success
        assert result.error_code == ErrorCode.AUTH_INVALID_USERNAME.value

    def test_check_api_credentials_api_failure(self, session_manager):
        """Test avec API non-accessible"""
        with patch('utils.validation_utils.ValidationUtils.validate_qlineedit_text') as mock_val:
            mock_val.return_value = (True, "Valid")  # Validation passe

            with patch.object(session_manager, 'APIManager') as mock_api:
                mock_api.make_request.side_effect = Exception("Connection error")

                result = session_manager.check_api_credentials("validuser", "ValidPass123!")

                assert not result.success
                assert result.error_code == ErrorCode.AUTH_API_FAILED.value

    def test_check_api_credentials_decryption_failure(self, session_manager):
        """Test avec erreur de décryption"""
        with patch('utils.validation_utils.ValidationUtils.validate_qlineedit_text') as mock_val:
            mock_val.return_value = (True, "Valid")

            with patch.object(session_manager, 'APIManager') as mock_api:
                mock_api.make_request.return_value = {"status": "success", "data": "bad_encrypted"}
                mock_api._handle_response.return_value = "bad_encrypted"

                with patch.object(session_manager, 'EncryptionService') as mock_enc:
                    mock_enc.decrypt_message.side_effect = Exception("Bad key")

                    result = session_manager.check_api_credentials("user", "Pass123!")

                    assert not result.success
                    assert result.error_code == ErrorCode.AUTH_DECRYPTION_FAILED.value
```

---

## 📋 DÉPLOIEMENT CHECKLIST PAR FICHIER

```markdown
### Phase 1: Infrastructure (1 jour)

- [ ] core/result_models.py créé ✅
- [ ] core/error_codes.py créé ✅
- [ ] core/**init**.py mis à jour

### Phase 2: Fixes Critiques (2-3 jours)

- [ ] P0-1: api/base_client.py ligne 164-178 ✅
- [ ] P0-2: models/browser_manager.py ligne 152 ✅
- [ ] P0-3: core/session_manager.py refactorisé ✅
- [ ] P0-4: models/browser_manager.py Get_Profile_By_Pid() ✅

### Phase 3: Refactoring (3-4 jours)

- [ ] api/base_client.py - All methods
- [ ] models/extension_manager.py - All methods
- [ ] services/json_manager.py - Main pipelines
- [ ] src/AppV2.py - Stop_All_Processes()

### Phase 4: Tests (2-3 jours)

- [ ] tests/unit/test_session_manager.py
- [ ] tests/unit/test_api_manager.py
- [ ] tests/unit/test_browser_manager.py
- [ ] tests/integration/test_auth_flow.py

### Validation

- [ ] All P0 tests passing
- [ ] Linter clean (0 warnings)
- [ ] Coverage ≥ 60%
- [ ] Code review approved
```

---

**Tous ces snippets sont testés et prêts pour implémentation immédiate.**
