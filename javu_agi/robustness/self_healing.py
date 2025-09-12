import random, time


class SelfHealing:
    def __init__(self, primary_model, backup_model, fail_threshold=0.5):
        self.primary = primary_model
        self.backup = backup_model
        self.fail_threshold = fail_threshold

    def _check_model_health(self, error_rate):
        """Check jika model primary terlalu sering gagal"""
        return error_rate < self.fail_threshold

    def switch_to_backup(self):
        """Switch ke model backup jika primary gagal."""
        print("Switching to backup model...")
        self.primary = self.backup

    def self_heal(self, error_rate):
        if not self._check_model_health(error_rate):
            self.switch_to_backup()
