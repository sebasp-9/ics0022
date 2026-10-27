class VaultError(Exception):
    """An expected error that can be safely shown without exposing secrets."""

    def __init__(self, message, code=1):
        super().__init__(message)
        self.code = code
