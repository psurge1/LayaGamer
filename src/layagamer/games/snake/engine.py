"""Immutable, step-based Snake rules."""
from dataclasses import dataclass
from collections import deque

Point = tuple[int, int]
DIRECTIONS: dict[str, Point] = {"up": (0, -1), "right": (1, 0), "down": (0, 1), "left": (-1, 0)}
TURNS = {
    "up": {"left": "left", "straight": "up", "right": "right"},
    "right": {"left": "up", "straight": "right", "right": "down"},
    "down": {"left": "right", "straight": "down", "right": "left"},
    "left": {"left": "down", "straight": "left", "right": "up"},
}


@dataclass(frozen=True)
class SnakeState:
    width: int = 10
    height: int = 10
    snake: tuple[Point, ...] = ((4, 5), (3, 5), (2, 5))
    direction: str = "right"
    food: Point = (7, 5)
    score: int = 0
    alive: bool = True

    def __post_init__(self) -> None:
        if not (4 <= self.width <= 30 and 4 <= self.height <= 30):
            raise ValueError("Snake board dimensions must be between 4 and 30")
        if not self.snake or len(set(self.snake)) != len(self.snake):
            raise ValueError("Snake segments must be nonempty and unique")
        if self.direction not in DIRECTIONS:
            raise ValueError("Invalid direction")
        if any(not self.in_bounds(point) for point in self.snake) or not self.in_bounds(self.food):
            raise ValueError("Snake or food is outside the board")
        if self.food in self.snake:
            raise ValueError("Food overlaps the snake")

    def in_bounds(self, point: Point) -> bool:
        return 0 <= point[0] < self.width and 0 <= point[1] < self.height

    def next_head(self, action: str) -> Point:
        if action not in TURNS[self.direction]:
            raise ValueError(f"Unknown relative action: {action}")
        direction = TURNS[self.direction][action]
        dx, dy = DIRECTIONS[direction]
        head = self.snake[0]
        return head[0] + dx, head[1] + dy

    def step(self, action: str, next_food: Point | None = None) -> "SnakeState":
        if not self.alive:
            raise ValueError("Cannot step a dead snake")
        head = self.next_head(action)
        grows = head == self.food
        occupied = self.snake if grows else self.snake[:-1]
        if not self.in_bounds(head) or head in occupied:
            return SnakeState(self.width, self.height, self.snake, self.direction,
                              self.food, self.score, False)
        snake = (head,) + (self.snake if grows else self.snake[:-1])
        food = self.food
        if grows:
            if next_food is None or not self.in_bounds(next_food) or next_food in snake:
                raise ValueError("Eating requires a valid next_food point")
            food = next_food
        return SnakeState(self.width, self.height, snake, TURNS[self.direction][action],
                          food, self.score + int(grows), True)

    def reachable_space(self, action: str) -> int:
        start = self.next_head(action)
        occupied = set(self.snake[:-1])
        if not self.in_bounds(start) or start in occupied:
            return 0
        queue, seen = deque([start]), {start}
        while queue:
            x, y = queue.popleft()
            for dx, dy in DIRECTIONS.values():
                point = x + dx, y + dy
                if self.in_bounds(point) and point not in occupied and point not in seen:
                    seen.add(point); queue.append(point)
        return len(seen)

    def shortest_food_path(self, start: Point) -> int | None:
        """Estimate the shortest route from a candidate head to the food."""
        if not self.in_bounds(start) or start in self.snake[:-1]:
            return None
        if start == self.food:
            return 0
        occupied = set(self.snake[:-1])
        queue = deque([(start, 0)])
        seen = {start}
        while queue:
            (x, y), distance = queue.popleft()
            for dx, dy in DIRECTIONS.values():
                point = x + dx, y + dy
                if point == self.food:
                    return distance + 1
                if self.in_bounds(point) and point not in occupied and point not in seen:
                    seen.add(point)
                    queue.append((point, distance + 1))
        return None

    def food_bearing(self) -> str:
        """Describe food position relative to the current heading."""
        head_x, head_y = self.snake[0]
        food_x, food_y = self.food
        forward_x, forward_y = DIRECTIONS[self.direction]
        right_x, right_y = -forward_y, forward_x
        delta_x, delta_y = food_x - head_x, food_y - head_y
        forward = delta_x * forward_x + delta_y * forward_y
        sideways = delta_x * right_x + delta_y * right_y
        longitudinal = "ahead" if forward > 0 else "behind" if forward < 0 else "level"
        lateral = "right" if sideways > 0 else "left" if sideways < 0 else "centered"
        if longitudinal == "level":
            return lateral
        if lateral == "centered":
            return f"directly_{longitudinal}"
        return f"{longitudinal}_{lateral}"

    def consequences(self) -> dict[str, dict]:
        current_distance = abs(self.snake[0][0] - self.food[0]) + abs(self.snake[0][1] - self.food[1])
        result = {}
        for action in ("left", "straight", "right"):
            head = self.next_head(action)
            distance = abs(head[0] - self.food[0]) + abs(head[1] - self.food[1])
            safe = self.in_bounds(head) and head not in self.snake[:-1]
            space = self.reachable_space(action)
            result[action] = {
                "resulting_direction": TURNS[self.direction][action],
                "next_head": list(head), "safe": safe, "eats_food": safe and head == self.food,
                "food_distance": distance, "moves_toward_food": distance < current_distance,
                "shortest_food_path": self.shortest_food_path(head) if safe else None,
                "reachable_space": space,
                "space_ratio": round(space / (self.width * self.height - len(self.snake) + 1), 3),
                "trap_risk": safe and space < max(6, len(self.snake) + 2),
            }
        path_lengths = [fact["shortest_food_path"] for fact in result.values()
                        if fact["safe"] and fact["shortest_food_path"] is not None]
        best_path = min(path_lengths, default=None)
        for fact in result.values():
            path = fact["shortest_food_path"]
            fact["on_shortest_food_route"] = best_path is not None and path == best_path
        return result

    def observation(self) -> dict:
        return {"width": self.width, "height": self.height,
                "snake": [list(point) for point in self.snake], "direction": self.direction,
                "food": list(self.food), "food_bearing": self.food_bearing(), "score": self.score}
