# 🧪 GUIDE DE VALIDATION & TESTING

## Stratégie de Vérification et de Validation

---

## 📊 MATRIX DE VALIDATION

```
┌─────────────────────────────────────────────────────────────┐
│ NIVEAU DE TEST       │ COUVERTURE    │ DURÉE   │ VALIDATEUR  │
├─────────────────────────────────────────────────────────────┤
│ 1. Syntaxe (Static)  │ 100%          │ 5 min   │ pylint      │
│ 2. Tests Unitaires   │ Chaque fonction│ 30 min  │ pytest      │
│ 3. Tests Intégration │ Workflows     │ 45 min  │ pytest      │
│ 4. Tests End-to-End  │ User stories  │ 1h 30   │ Manual      │
│ 5. Regression        │ Critical flow │ 1h      │ pytest      │
└─────────────────────────────────────────────────────────────┘
```

---

## 🐍 SECTION 1: VALIDATION SYNTAXE CRITIQUES

### Test 1.1: Vérifier les imports essentiels

**Fichier**: `checkV3.py` (ligne 1-50)

```python
# Script de validation
import ast
import sys

def validate_imports(filepath: str) -> bool:
    """Vérifie que tous les imports critiques sont présents"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read())

        required_imports = {
            'os', 'sys', 'json', 'asyncio', 'subprocess'
        }

        found_imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    found_imports.add(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    found_imports.add(node.module.split('.')[0])

        missing = required_imports - found_imports
        if missing:
            print(f"❌ Imports manquants: {missing}")
            return False

        print("✅ Tous les imports essentiels présents")
        return True

    except SyntaxError as e:
        print(f"❌ Erreur syntaxe: {e}")
        return False

# Exécuter
if __name__ == "__main__":
    result = validate_imports("checkV3.py")
    sys.exit(0 if result else 1)
```

**Commande**:

```bash
cd d:\Automation Gmail - Copie
python -m py_compile checkV3.py
python -m py_compile api/base_client.py
python -m py_compile core/session_manager.py
python -m py_compile models/browser_manager.py
```

**Résultat attendu**:

```
✅ checkV3.py compiled successfully
✅ api/base_client.py compiled successfully
✅ core/session_manager.py compiled successfully
✅ models/browser_manager.py compiled successfully
```

---

### Test 1.2: Vérifier les typos critiques

```python
# Script de détection de typos

import re

typos = {
    r"os\.pa\(": "os.path() ou os.pa... - TYPO TROUVÉ",
    r"os\.pa ": "os.path avec espace - TYPO TROUVÉ",
    r"except \\w+:": "Bare except trouvé",
    r"return None": "Retourne None (ambiguë si succès/erreur)",
}

def check_typos(filepath: str):
    """Scan pour les typos/patterns critiques"""
    with open(filepath, 'r') as f:
        content = f.read()
        lines = content.split('\n')

    issues = []
    for line_no, line in enumerate(lines, 1):
        for pattern, desc in typos.items():
            if re.search(pattern, line):
                issues.append(f"Ligne {line_no}: {desc} - {line.strip()}")

    return issues

# CHECK KEY FILES
for file in ["api/base_client.py", "models/browser_manager.py", "core/session_manager.py"]:
    print(f"\n📄 Checking {file}...")
    issues = check_typos(file)
    if issues:
        for issue in issues:
            print(f"  ⚠️  {issue}")
    else:
        print(f"  ✅ No issues found")
```

**Résultat attendu**: AVANT correction = warnings, APRÈS = clean

---

## 📝 SECTION 2: TESTS UNITAIRES

### Test 2.1: Validateurs de Session

```python
# tests/test_session_validation.py

import pytest
from unittest.mock import patch, MagicMock
from core.session_manager import SessionManager
from core.result_models import Result, ResultStatus
from core.error_codes import ErrorCode

class TestSessionValidation:
    """Tests de validation de session"""

    @pytest.fixture
    def mock_dependencies(self):
        """Mock des dépendances"""
        with patch('core.session_manager.EncryptionService'), \
             patch('core.session_manager.APIManager'), \
             patch('core.session_manager.settings') as mock_settings:
            mock_settings.WRITE_LOG_DEV_FILE = MagicMock()
            yield {
                'settings': mock_settings
            }

    def test_result_success(self):
        """Result.success() fonctionne"""
        result = Result.success(data={"user": "test"})
        assert result.is_success
        assert result.data == {"user": "test"}
        assert str(result) == "Result(SUCCESS, error=None)"

    def test_result_failure(self):
        """Result.failure() crée erreur"""
        result = Result.failure(
            error="Test error",
            error_code="TEST_001"
        )
        assert result.is_failure
        assert result.error == "Test error"
        assert result.error_code == "TEST_001"
        assert not result.is_success

    def test_result_validation_error(self):
        """Result.validation_error() pour inputs"""
        result = Result.validation_error(
            "Invalid email",
            details={"field": "email"}
        )
        assert result.status == ResultStatus.VALIDATION_ERROR
        assert result.error_code == "VALIDATION_ERROR"
        assert result.details["field"] == "email"

    def test_result_bool_conversion(self):
        """Result peut être utilisé en if"""
        success = Result.success(data=42)
        failure = Result.failure("error")

        assert bool(success) is True
        assert bool(failure) is False

        # Test d'utilisation réelle
        if success:
            assert success.data == 42

        if not failure:
            assert failure.error == "error"

    def test_result_to_json(self):
        """Result peut être sérialisé en JSON"""
        result = Result.success(data={"id": 123})
        json_str = result.to_json()

        assert '"status": "SUCCESS"' in json_str
        assert '"data": {"id": 123}' in json_str or 'id' in json_str
```

**Exécution**:

```bash
cd d:\Automation Gmail - Copie
pip install pytest
pytest tests/test_session_validation.py -v
```

**Résultat attendu**:

```
test_result_success PASSED
test_result_failure PASSED
test_result_validation_error PASSED
test_result_bool_conversion PASSED
test_result_to_json PASSED

5 passed in 0.23s ✅
```

---

### Test 2.2: API Response Handling

```python
# tests/test_api_fixes.py

import pytest
from unittest.mock import Mock, patch
from api.base_client import APIManager

class TestAPIFixes:
    """Tests pour les corrections API"""

    def test_on_scenario_changed_no_undefined_response(self):
        """
        P0-1: Vérifier que 'response' est définie avant utilisation
        (Prévient NameError ligne 164)
        """
        api = APIManager()

        with patch.object(api, 'make_request') as mock_request:
            mock_request.return_value = {"success": True}

            with patch.object(api, '_handle_response') as mock_handle:
                mock_handle.return_value = {"success": True, "id": 1}

                # Ne doit pas lever NameError
                result = api.on_scenario_changed(
                    {"process": "test"},
                    "http://api.test/scenario"
                )

                # Vérifier que le résultat est correct
                assert "success" in result
                mock_request.assert_called_once()

    def test_on_scenario_changed_exception_handling(self):
        """on_scenario_changed gère les exceptions correctement"""
        api = APIManager()

        with patch.object(api, 'make_request') as mock_request:
            mock_request.side_effect = Exception("Connection failed")

            result = api.on_scenario_changed(
                {"process": "test"},
                "http://api.test/scenario"
            )

            assert result.get("success") is False
            assert "error" in result or "Connection" in str(result)

    def test_save_process_return_type(self):
        """
        save_process() retourne toujours un type consistant
        (Prévient ambiguïté du retour -1)
        """
        api = APIManager()

        # Mock response
        with patch.object(api, 'make_request') as mock_request:
            mock_request.return_value = {"id": 123, "status": "saved"}

            with patch.object(api, '_handle_response') as mock_handle:
                mock_handle.return_value = 123

                result = api.save_process({
                    "process": "login",
                    "email": "test@example.com"
                })

                # Si le résultat est entier, vérifier interprétation
                assert isinstance(result, int)
                assert result > 0  # Negate ambiguïté
```

---

## 🔍 SECTION 3: TESTS D'INTÉGRATION

### Test 3.1: Workflow Authentification Complet

```python
# tests/integration/test_auth_workflow.py

import pytest
from unittest.mock import Mock, patch, MagicMock
from core.session_manager import SessionManager, CredentialCheckResult
from core.error_codes import ErrorCode
from utils.validation_utils import ValidationUtils

class TestAuthWorkflow:
    """Tests du workflow d'authentification complet"""

    def test_full_login_flow_success(self):
        """Workflow: User login → Validation → API check → Decryption"""

        # 1️⃣ Créer SessionManager avec dépendances mockées
        with patch('core.session_manager.EncryptionService') as MockEnc, \
             patch('core.session_manager.APIManager') as MockAPI, \
             patch('core.session_manager.settings') as mock_settings:

            mock_settings.WRITE_LOG_DEV_FILE = MagicMock()

            # 2️⃣ Configurer les mocks
            MockAPI.make_request.return_value = {
                "status": 200,
                "data": "encrypted_response"
            }
            MockAPI._handle_response.return_value = "encrypted_response"

            # ID=42, entity=prod (vrai format attendu)
            MockEnc.decrypt_message.return_value = "42;prod"

            # 3️⃣ Exécuter le login
            sm = SessionManager()
            result = sm.check_api_credentials("validuser", "ValidPass123!")

            # 4️⃣ Assertions
            assert isinstance(result, CredentialCheckResult)
            assert result.success is True
            assert result.data.user_id == "42"
            assert result.data.entity == "prod"
            assert result.error is None

    def test_full_login_flow_invalid_user(self):
        """Workflow: Reject invalid username"""

        sm = SessionManager()
        result = sm.check_api_credentials("ab", "ValidPassword123")

        assert result.success is False
        assert result.error_code == ErrorCode.AUTH_INVALID_USERNAME.value
        assert "minimum" in result.error.lower() or "invalid" in result.error.lower()

    def test_full_login_flow_api_failure(self):
        """Workflow: Handle API connection failure"""

        with patch('core.session_manager.APIManager') as MockAPI, \
             patch('core.session_manager.settings') as mock_settings:

            # API est down
            MockAPI.make_request.side_effect = ConnectionError("API unreachable")
            mock_settings.WRITE_LOG_DEV_FILE = MagicMock()

            sm = SessionManager()
            result = sm.check_api_credentials("validuser", "ValidPass123!")

            assert result.success is False
            assert result.error_code == ErrorCode.AUTH_API_FAILED.value
            assert "attempt" in result.error.lower()  # Retry logic

    def test_full_login_flow_invalid_decryption(self):
        """Workflow: Handle decryption failure"""

        with patch('core.session_manager.APIManager') as MockAPI, \
             patch('core.session_manager.EncryptionService') as MockEnc, \
             patch('core.session_manager.settings') as mock_settings:

            MockAPI.make_request.return_value = {"data": "encrypted"}
            MockAPI._handle_response.return_value = "encrypted"
            MockEnc.decrypt_message.side_effect = ValueError("Bad key")
            mock_settings.WRITE_LOG_DEV_FILE = MagicMock()

            sm = SessionManager()
            result = sm.check_api_credentials("validuser", "ValidPass123!")

            assert result.success is False
            assert result.error_code == ErrorCode.AUTH_DECRYPTION_FAILED.value

    def test_full_login_flow_invalid_decrypted_format(self):
        """Workflow: Handle malformed decrypted data"""

        with patch('core.session_manager.APIManager') as MockAPI, \
             patch('core.session_manager.EncryptionService') as MockEnc, \
             patch('core.session_manager.settings') as mock_settings:

            MockAPI.make_request.return_value = {"data": "encrypted"}
            MockAPI._handle_response.return_value = "encrypted"
            MockEnc.decrypt_message.return_value = "INVALID_FORMAT_NO_SEMICOLON"
            mock_settings.WRITE_LOG_DEV_FILE = MagicMock()

            sm = SessionManager()
            result = sm.check_api_credentials("validuser", "ValidPass123!")

            assert result.success is False
            assert result.error_code == ErrorCode.AUTH_DECRYPTION_FAILED.value

    def test_full_login_flow_zero_user_id(self):
        """Workflow: Reject user_id=0 (doit être > 0)"""

        with patch('core.session_manager.APIManager') as MockAPI, \
             patch('core.session_manager.EncryptionService') as MockEnc, \
             patch('core.session_manager.settings') as mock_settings:

            MockAPI.make_request.return_value = {"data": "encrypted"}
            MockAPI._handle_response.return_value = "encrypted"
            MockEnc.decrypt_message.return_value = "0;prod"  # ID=0 invalide
            mock_settings.WRITE_LOG_DEV_FILE = MagicMock()

            sm = SessionManager()
            result = sm.check_api_credentials("validuser", "ValidPass123!")

            assert result.success is False
            assert result.error_code == ErrorCode.AUTH_CREDENTIALS_INVALID.value

    def test_full_login_flow_empty_entity(self):
        """Workflow: Reject empty entity"""

        with patch('core.session_manager.APIManager') as MockAPI, \
             patch('core.session_manager.EncryptionService') as MockEnc, \
             patch('core.session_manager.settings') as mock_settings:

            MockAPI.make_request.return_value = {"data": "encrypted"}
            MockAPI._handle_response.return_value = "encrypted"
            MockEnc.decrypt_message.return_value = "42;"  # Entity vide
            mock_settings.WRITE_LOG_DEV_FILE = MagicMock()

            sm = SessionManager()
            result = sm.check_api_credentials("validuser", "ValidPass123!")

            assert result.success is False
            assert result.error_code == ErrorCode.AUTH_CREDENTIALS_INVALID.value

# Exécution
if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
```

**Exécution**:

```bash
pytest tests/integration/test_auth_workflow.py -v -s
```

---

## ✅ SECTION 4: CHECKLIST DE VALIDATION FINALE

### Avant Chaque Fix

```markdown
## 📋 Checklist Pré-Fix

- [ ] Comprendre le problème via `ANALYSE_CODE_PROFONDE.md`
- [ ] Localiser le fichier et la ligne exacte
- [ ] Créer une branche git: `git checkout -b fix/P0-1-nameError`
- [ ] Sauvegarder la version originale (snapshot)
- [ ] Identifier tous les callers du code modifié
- [ ] Préparer les tests unitaires
- [ ] Lire la section "Validation" ci-dessous
```

### Après Chaque Fix

```markdown
## ✅ Checklist Post-Fix

- [ ] Syntaxe valide: `python -m py_compile [file]`
- [ ] Pas d'erreur import: `python -c "from module import *"`
- [ ] Tests passent: `pytest tests/test_[module].py -v`
- [ ] No regression: Relancer tests des modules dependants
- [ ] Lint clean: `pylint [file]` (< 8.0 score acceptable)
- [ ] Code review effectuée
- [ ] Commit avec message explicite
- [ ] Merge en develop après tests
```

---

## 🚀 SECTION 5: ORDRE D'IMPLÉMENTATION RECOMMANDÉ

```
JOUR 1 (8h) - Créer Infrastructure
├─ 0h00-0h30: Créer core/result_models.py
├─ 0h30-0h45: Créer core/error_codes.py
├─ 0h45-1h15: Tester Result & ErrorCode (Test 2.1)
├─ 1h15-2h00: Intégrer dans tous les imports
└─ 2h00-8h00: Fix P0 critiques (3-4 heures par fix + tests)

JOUR 2 (8h) - Fix P0-1, P0-2
├─ 0h00-0h30: P0-1 (NameError route 164) + Test
├─ 0h30-1h00: P0-2 (os.pa typo) + Test
├─ 1h00-2h00: P0-3 (session_manager refactor) + Tests intégration
├─ 2h00-4h00: P0-4 (exception masking) + Tests
└─ 4h00-8h00: Valider tout fonctionne ensemble

JOUR 3 (8h) - Tests Régression
├─ 0h00-2h00: Tests unitaires complètes
├─ 2h00-4h00: Tests d'intégration (Test 3.1)
├─ 4h00-6h00: Manual smoke testing
└─ 6h00-8h00: Documentation des changes
```

---

## 📊 MATRICE DE SUCCÈS

```
MÉTRIQUE                    | AVANT  | CIBLE  | STATUS
────────────────────────────────────────────────
Functions avec None ambigus | 18     | 0      | ❌→✅
Type inconsistencies        | 6      | 0      | ❌→✅
Exception swallowing        | 8      | 0      | ❌→✅
Test coverage              | 15%    | 60%    | ❌→✅
Linter score                | 5.2    | 8.0+   | ❌→✅
Critical bugs               | 6      | 0      | ❌→✅
```

---

**Valider chaque étape avant de passer à la suivante !**
