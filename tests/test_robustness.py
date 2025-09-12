def test_self_healing():
    error_rate = 0.7  # Error tinggi untuk trigger fallback
    self.self_healer.self_heal(error_rate)
    assert self.model != self.backup_model
