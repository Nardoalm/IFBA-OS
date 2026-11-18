"""Validated, non-secret per-user assistant preferences."""

import json
import os
import tempfile


DEFAULTS = {
    "model_id": "deepseek-ai/deepseek-v4.1-flash",
    "max_tokens": 2048,
    "memory_enabled": False,
    "share_active_application": False,
    "share_system_profile": False,
    "education_level": "iniciante",
    "context_max_messages": 24,
    "context_max_chars": 24000,
    "history_retention_days": 365,
    "memory_retention_days": 365,
}


class SettingsError(ValueError):
    pass


def validate_settings(values):
    if not isinstance(values, dict):
        raise SettingsError("As configurações precisam ser um objeto.")
    unknown = set(values) - set(DEFAULTS)
    if unknown:
        raise SettingsError("Uma configuração não reconhecida foi enviada.")
    result = dict(DEFAULTS)
    result.update(values)
    model = result["model_id"]
    if not isinstance(model, str) or not model.strip() or len(model) > 256:
        raise SettingsError("Selecione um identificador de modelo válido.")
    try:
        limit = int(result["max_tokens"])
    except (TypeError, ValueError):
        raise SettingsError("O limite de tokens deve ser um número.")
    if limit < 1 or limit > 32768:
        raise SettingsError("O limite configurável deve ficar entre 1 e 32768 tokens.")
    for key in ("memory_enabled", "share_active_application", "share_system_profile"):
        if not isinstance(result[key], bool):
            raise SettingsError("Uma preferência contém um tipo inválido.")
    if result["education_level"] not in ("iniciante", "intermediario", "avancado"):
        raise SettingsError("Escolha um nível de aprendizagem válido.")
    for key, lower, upper in (("context_max_messages", 2, 100), ("context_max_chars", 1000, 100000),
                              ("history_retention_days", 0, 3650), ("memory_retention_days", 0, 3650)):
        try:
            value = int(result[key])
        except (TypeError, ValueError):
            raise SettingsError("Um limite de contexto ou retenção é inválido.")
        if value < lower or value > upper:
            raise SettingsError("Um limite de contexto ou retenção está fora da faixa permitida.")
        result[key] = value
    result["model_id"] = model.strip()
    result["max_tokens"] = limit
    return result


class SettingsStore:
    def __init__(self, paths):
        self.paths = paths

    def read(self):
        self.paths.prepare()
        try:
            with open(str(self.paths.settings), "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except FileNotFoundError:
            return dict(DEFAULTS)
        except (OSError, ValueError) as error:
            raise SettingsError("Não foi possível ler as configurações do assistente.") from error
        return validate_settings(data)

    def write(self, values):
        self.paths.prepare()
        data = validate_settings(values)
        fd, temporary = tempfile.mkstemp(prefix="settings-", dir=str(self.paths.config))
        try:
            os.fchmod(fd, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(data, handle, ensure_ascii=False, indent=2)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, str(self.paths.settings))
            os.chmod(str(self.paths.settings), 0o600)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
        return data
