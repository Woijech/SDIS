from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class WaveEntry:
    """Single enemy spawn instruction inside a wave."""

    enemy: str
    count: int
    interval: float


@dataclass(slots=True)
class WavePlan:
    """Fully parsed description of one wave."""

    number: int
    entries: list[WaveEntry]
    clear_delay: float = 2.0


def build_wave_plans(raw_waves: list[dict]) -> list[WavePlan]:
    """Convert raw JSON wave payloads into typed wave plans.

    Args:
        raw_waves: Wave entries loaded from ``waves.json``.

    Returns:
        Parsed wave plans ready to be consumed by ``WaveController``.
    """
    plans: list[WavePlan] = []
    for raw_wave in raw_waves:
        entries = [
            WaveEntry(
                enemy=item["enemy"],
                count=int(item["count"]),
                interval=float(item["interval"]),
            )
            for item in raw_wave["entries"]
        ]
        plans.append(
            WavePlan(
                number=int(raw_wave["number"]),
                entries=entries,
                clear_delay=float(raw_wave.get("clear_delay", 2.0)),
            )
        )
    return plans


class WaveController:
    """Spawns enemies according to wave configs."""

    def __init__(self, waves: list[WavePlan]) -> None:
        """Initialize controller state for a prepared wave list.

        Args:
            waves: Ordered list of parsed wave plans.

        Returns:
            None. The controller starts idle until ``start`` is called.

        Raises:
            ValueError: If no waves are provided.
        """
        if not waves:
            raise ValueError("At least one wave is required")
        self.waves = waves
        self.current_wave_index = -1
        self.current_entry_index = 0
        self.remaining_in_entry = 0
        self.spawn_timer = 0.0
        self.waiting_for_clear = False
        self.inter_wave_timer = 0.0
        self.finished = False
        self.started = False
        self.wave_started_this_frame = False
        self.wave_completed_this_frame = False
        self.current_wave: WavePlan | None = None

    def start(self) -> None:
        """Start the wave sequence from the first configured wave.

        Returns:
            None. Repeated calls after startup are ignored.
        """
        if self.started:
            return
        self.started = True
        self._begin_wave(0)

    def _begin_wave(self, index: int) -> None:
        """Switch controller state to a specific wave index.

        Args:
            index: Zero-based index of the wave that should become active.

        Returns:
            None. Internal spawn counters are reset for the new wave.
        """
        self.current_wave_index = index
        self.current_wave = self.waves[index]
        self.current_entry_index = 0
        self.remaining_in_entry = self.current_wave.entries[0].count
        self.spawn_timer = 0.0
        self.waiting_for_clear = False
        self.inter_wave_timer = 0.0
        self.wave_started_this_frame = True

    @property
    def current_wave_number(self) -> int:
        """Return the one-based number of the active wave.

        Returns:
            Current wave number, or ``0`` when no wave is active yet.
        """
        if self.current_wave is None:
            return 0
        return self.current_wave.number

    @property
    def total_waves(self) -> int:
        """Return the total number of configured waves.

        Returns:
            Count of wave plans owned by the controller.
        """
        return len(self.waves)

    def update(self, dt: float, alive_enemy_count: int) -> list[str]:
        """Advance timers and return enemies that should spawn this frame.

        Args:
            dt: Frame delta time in seconds.
            alive_enemy_count: Number of enemies currently alive in the arena.

        Returns:
            List of enemy identifiers that should be spawned during this update.
        """
        self.wave_started_this_frame = False
        self.wave_completed_this_frame = False

        if self.finished or not self.started or self.current_wave is None:
            return []

        if self.inter_wave_timer > 0:
            self.inter_wave_timer -= dt
            if self.inter_wave_timer <= 0:
                next_index = self.current_wave_index + 1
                if next_index >= len(self.waves):
                    self.finished = True
                else:
                    self._begin_wave(next_index)
            return []

        if self.waiting_for_clear:
            if alive_enemy_count == 0:
                self.wave_completed_this_frame = True
                self.inter_wave_timer = self.current_wave.clear_delay
                self.waiting_for_clear = False
            return []

        spawned: list[str] = []
        self.spawn_timer -= dt

        while self.spawn_timer <= 0 and not self.waiting_for_clear:
            current_entry = self.current_wave.entries[self.current_entry_index]
            if self.remaining_in_entry > 0:
                spawned.append(current_entry.enemy)
                self.remaining_in_entry -= 1
                self.spawn_timer += current_entry.interval
            if self.remaining_in_entry == 0:
                self.current_entry_index += 1
                if self.current_entry_index >= len(self.current_wave.entries):
                    self.waiting_for_clear = True
                    break
                next_entry = self.current_wave.entries[self.current_entry_index]
                self.remaining_in_entry = next_entry.count

        return spawned

    def remaining_to_spawn(self) -> int:
        """Count how many enemies are still queued in the active wave.

        Returns:
            Number of enemies that have not been spawned yet for the current
            wave. Returns ``0`` when no wave is active.
        """
        if self.current_wave is None:
            return 0
        total = self.remaining_in_entry
        for entry in self.current_wave.entries[self.current_entry_index + 1 :]:
            total += entry.count
        return total
