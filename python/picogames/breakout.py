"""Breakout game model for PicoCalc framebuffer apps."""

from __future__ import annotations

from dataclasses import dataclass
import random


@dataclass
class Brick:
    x: int
    y: int
    width: int
    height: int
    color: int
    alive: bool = True


class BreakoutGame:
    """Small deterministic Breakout model with PicoCalc-sized defaults."""

    def __init__(
        self,
        *,
        width: int = 320,
        height: int = 320,
        rng: random.Random | None = None,
    ) -> None:
        self.width = width
        self.height = height
        self.rng = rng or random.Random()
        self.paddle_width = 40
        self.paddle_height = 5
        self.paddle_speed = 10.0
        self.ball_radius = 2
        self.brick_rows = 5
        self.brick_cols = 10
        self.brick_width = 30
        self.brick_height = 10
        self.brick_gap = 2
        self.status_height = 20
        self.initial_ball_speed = 4.75
        self.max_ball_speed = 7.0
        self.brick_colors = [0xF800, 0xFD20, 0xFFE0, 0x07E0, 0x039F]
        self.restart()

    @property
    def paddle_y(self) -> int:
        return self.height - self.paddle_height - self.status_height

    @property
    def bricks_remaining(self) -> int:
        return sum(1 for brick in self.bricks if brick.alive)

    @property
    def message(self) -> str:
        if self.won:
            return "YOU WIN! SPACE again"
        if self.game_over:
            return "GAME OVER - SPACE again"
        if not self.active:
            return "SPACE to begin"
        return ""

    def restart(self) -> None:
        self.score = 0
        self.lives = 3
        self.active = False
        self.game_over = False
        self.won = False
        self.ball_dx = 0.0
        self.ball_dy = 0.0
        self.ball_speed = self.initial_ball_speed
        self.paddle_x = float((self.width - self.paddle_width) // 2)
        self.last_hit_brick: Brick | None = None
        self.bricks = self._create_bricks()
        self.reset_ball()

    def _create_bricks(self) -> list[Brick]:
        bricks: list[Brick] = []
        total_width = self.brick_cols * (self.brick_width + self.brick_gap) - self.brick_gap
        start_x = (self.width - total_width) // 2
        for row in range(self.brick_rows):
            for col in range(self.brick_cols):
                bricks.append(
                    Brick(
                        x=start_x + col * (self.brick_width + self.brick_gap),
                        y=30 + row * (self.brick_height + self.brick_gap),
                        width=self.brick_width,
                        height=self.brick_height,
                        color=self.brick_colors[row % len(self.brick_colors)],
                    )
                )
        return bricks

    def reset_ball(self) -> None:
        self.ball_x = float(self.width // 2)
        self.ball_y = float(self.paddle_y - self.ball_radius * 3)
        self.ball_dx = 0.0
        self.ball_dy = 0.0

    def launch(self) -> None:
        if self.game_over or self.won:
            self.restart()
        self.active = True
        self.ball_speed = self.initial_ball_speed
        angle = self.rng.uniform(0.5, 0.8)
        self.ball_dx = self.ball_speed * self.rng.choice([-angle, angle])
        self.ball_dy = -self.ball_speed * (1 - abs(self.ball_dx / self.ball_speed))

    def move_paddle(self, direction: str, *, amount: float | None = None) -> None:
        amount = self.paddle_speed if amount is None else float(amount)
        if direction == "left":
            self.paddle_x = max(0.0, self.paddle_x - amount)
        elif direction == "right":
            self.paddle_x = min(float(self.width - self.paddle_width), self.paddle_x + amount)
        if not self.active:
            self.ball_x = self.paddle_x + self.paddle_width // 2

    def step(self, dt: float = 1 / 60) -> list[str]:
        del dt
        events: list[str] = []
        if not self.active or self.game_over or self.won:
            self.ball_x = self.paddle_x + self.paddle_width // 2
            return events

        self.ball_x += self.ball_dx
        self.ball_y += self.ball_dy

        if self.ball_x - self.ball_radius <= 0:
            self.ball_x = self.ball_radius + 1
            self.ball_dx = abs(self.ball_dx)
            events.append("wall")
        elif self.ball_x + self.ball_radius >= self.width:
            self.ball_x = self.width - self.ball_radius - 1
            self.ball_dx = -abs(self.ball_dx)
            events.append("wall")

        if self.ball_y - self.ball_radius <= 0:
            self.ball_y = self.ball_radius + 1
            self.ball_dy = abs(self.ball_dy)
            events.append("wall")

        if self.ball_y + self.ball_radius > self.height - self.status_height:
            self.lives -= 1
            events.append("life_lost")
            self.active = False
            if self.lives <= 0:
                self.game_over = True
                events.append("game_over")
            self.reset_ball()
            return events

        if self._paddle_collision():
            hit_position = (self.ball_x - self.paddle_x) / self.paddle_width
            angle_factor = max(-1.0, min(1.0, 2 * (hit_position - 0.5)))
            self.ball_speed = min(self.ball_speed * 1.05, self.max_ball_speed)
            self.ball_dx = self.ball_speed * angle_factor
            self.ball_dy = -self.ball_speed * (1 - 0.8 * abs(angle_factor))
            self.ball_y = self.paddle_y - self.ball_radius - 1
            events.append("paddle")

        brick = self._colliding_brick()
        if brick is not None:
            self._hit_brick(brick)
            events.append("brick")
            if self.bricks_remaining == 0:
                self.active = False
                self.game_over = True
                self.won = True
                events.append("won")

        if self.last_hit_brick and not self._brick_collision(self.last_hit_brick):
            self.last_hit_brick = None
        return events

    def _paddle_collision(self) -> bool:
        return (
            self.ball_y + self.ball_radius >= self.paddle_y
            and self.ball_y - self.ball_radius <= self.paddle_y + self.paddle_height
            and self.ball_x + self.ball_radius >= self.paddle_x
            and self.ball_x - self.ball_radius <= self.paddle_x + self.paddle_width
        )

    def _brick_collision(self, brick: Brick) -> bool:
        return (
            brick.alive
            and brick.x <= self.ball_x + self.ball_radius
            and brick.x + brick.width >= self.ball_x - self.ball_radius
            and brick.y <= self.ball_y + self.ball_radius
            and brick.y + brick.height >= self.ball_y - self.ball_radius
        )

    def _colliding_brick(self) -> Brick | None:
        for brick in self.bricks:
            if brick is self.last_hit_brick:
                continue
            if self._brick_collision(brick):
                return brick
        return None

    def _hit_brick(self, brick: Brick) -> None:
        self.last_hit_brick = brick
        brick.alive = False
        dx1 = self.ball_x - brick.x
        dx2 = brick.x + brick.width - self.ball_x
        dy1 = self.ball_y - brick.y
        dy2 = brick.y + brick.height - self.ball_y
        min_dist = min(dx1, dx2, dy1, dy2)
        if min_dist in (dy1, dy2):
            self.ball_dy = -self.ball_dy
        else:
            self.ball_dx = -self.ball_dx
        self.score += 10
