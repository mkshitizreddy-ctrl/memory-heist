class SecurityMeter:
    def __init__(self, max_level: int = 100):
        self.level = 0
        self.max_level = max_level

    def increase(self, amount: int = 20):
        self.level = min(self.max_level, self.level + amount)

    def is_lockdown(self) -> bool:
        return self.level >= self.max_level

    def reset(self):
        self.level = 0
