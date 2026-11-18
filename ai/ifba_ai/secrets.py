"""Secret Service adapter. There is deliberately no plaintext fallback."""

import getpass
import shutil
import subprocess


class CredentialStoreError(RuntimeError):
    pass


class SecretStore:
    def __init__(self, executable="secret-tool", runner=subprocess.run, username=None):
        self.executable = executable
        self.runner = runner
        self.username = username or getpass.getuser()

    def _base(self, action):
        if shutil.which(self.executable) is None:
            raise CredentialStoreError("O cofre de credenciais Secret Service não está disponível.")
        return [self.executable, action, "service", "ifba-os", "account", self.username,
                "purpose", "nvidia-api-key"]

    def is_configured(self):
        return bool(self.get())

    def store(self, secret):
        if (not isinstance(secret, str) or not secret.strip() or "\n" in secret
                or "\r" in secret or len(secret) > 4096):
            raise ValueError("A chave está vazia ou tem formato inválido.")
        command = self._base("store")
        command.insert(2, "--label=IFBA OS NVIDIA API key")
        try:
            result = self.runner(command, input=secret, text=True, capture_output=True, timeout=15)
        except (OSError, subprocess.TimeoutExpired) as error:
            raise CredentialStoreError("Não foi possível acessar o cofre de credenciais.") from error
        if result.returncode != 0:
            raise CredentialStoreError("O cofre está bloqueado ou recusou o armazenamento da chave.")

    def get(self):
        try:
            result = self.runner(self._base("lookup"), text=True, capture_output=True, timeout=10)
        except (OSError, subprocess.TimeoutExpired) as error:
            raise CredentialStoreError("Não foi possível acessar o cofre de credenciais.") from error
        if result.returncode != 0:
            if not result.stderr.strip():
                return None
            raise CredentialStoreError("O cofre está bloqueado ou indisponível.")
        return result.stdout.rstrip("\r\n")

    def delete(self):
        try:
            result = self.runner(self._base("clear"), text=True, capture_output=True, timeout=10)
        except (OSError, subprocess.TimeoutExpired) as error:
            raise CredentialStoreError("Não foi possível acessar o cofre de credenciais.") from error
        if result.returncode != 0:
            raise CredentialStoreError("Não foi possível remover a chave do cofre.")
