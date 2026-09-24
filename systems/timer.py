class Timer:
    def __init__(self, seconds: float = 0):
        self.remaining = seconds
        self.active = False

    def start(self, seconds: float):
        self.remaining = seconds
        self.active = True

    def update(self, dt: float):
        if self.active:
            self.remaining = max(0.0, self.remaining - dt)

    def expired(self) -> bool:
        return self.active and self.remaining <= 0

    def get_remaining(self) -> float:
        return self.remaining
