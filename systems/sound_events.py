"""
systems/sound_events.py
Owner: Member 1 - Core Game System

Plays the sound effects from one place, so no level has to call the audio
system itself. Once per frame the game hands over a snapshot of its state
and this class compares it with the previous one:

  security went up                      -> "wrong"
  score went up (and security did not)  -> "correct"
  a gate opened (level.gates_passed up) -> "unlock"
  a level was cleared or the run won    -> "unlock"
  the run was lost                      -> "wrong"
  a key on a menu or story card         -> "click" (Game calls click())

Starting a run or retrying resets score and security to zero; that is a
drop, never a rise, so it stays silent.
"""


class SoundEvents:
    def __init__(self, audio):
        self.audio = audio
        self._previous = None

    def click(self):
        self.audio.play("click")

    def observe(self, state, score, security, level, gates=0):
        """Compare this frame with the last one and play what happened."""
        current = (state, score, security, level, gates)
        previous, self._previous = self._previous, current
        if previous is None:
            return

        old_state, old_score, old_security, old_level, old_gates = previous

        if old_state == "playing" and state != "playing":
            # The run just left play: lost, or a level / the whole run cleared.
            self.audio.play("wrong" if state == "lose" else "unlock")
            return

        if state != "playing" or old_state != "playing":
            return

        if level != old_level or gates > old_gates:
            # Next level without a story card, or a gate just opened.
            self.audio.play("unlock")
        elif security > old_security:
            self.audio.play("wrong")
        elif score > old_score:
            self.audio.play("correct")
