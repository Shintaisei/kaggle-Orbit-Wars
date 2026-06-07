import math


CENTER_X = 50.0
CENTER_Y = 50.0
SUN_RADIUS = 10.0
STATIC_LIMIT = 50.0
MAX_SPEED = 6.0


ID = 0
OWNER = 1
X = 2
Y = 3
RADIUS = 4
SHIPS = 5
PRODUCTION = 6


def _get(obs, name, default=None):
    if isinstance(obs, dict):
        return obs.get(name, default)
    return getattr(obs, name, default)


def _distance(a, b):
    return math.hypot(a[X] - b[X], a[Y] - b[Y])


def _center_distance(p):
    return math.hypot(p[X] - CENTER_X, p[Y] - CENTER_Y)


def _is_static(p):
    return _center_distance(p) + p[RADIUS] >= STATIC_LIMIT


def _fleet_speed(ships):
    ships = max(int(ships), 1)
    speed = 1.0 + (MAX_SPEED - 1.0) * (math.log(ships) / math.log(1000)) ** 1.5
    return min(speed, MAX_SPEED)


def _point_segment_distance(px, py, ax, ay, bx, by):
    dx = bx - ax
    dy = by - ay
    if dx == 0.0 and dy == 0.0:
        return math.hypot(px - ax, py - ay)
    t = ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))
    cx = ax + t * dx
    cy = ay + t * dy
    return math.hypot(px - cx, py - cy)


def _crosses_sun(source, target):
    clearance = SUN_RADIUS + 0.35
    d = _point_segment_distance(
        CENTER_X,
        CENTER_Y,
        source[X],
        source[Y],
        target[X],
        target[Y],
    )
    return d <= clearance


def _path_clear(source, target, planets):
    if _crosses_sun(source, target):
        return False

    for p in planets:
        if p[ID] == source[ID] or p[ID] == target[ID]:
            continue
        d = _point_segment_distance(
            p[X],
            p[Y],
            source[X],
            source[Y],
            target[X],
            target[Y],
        )
        if d < p[RADIUS] + 0.2:
            return False

    return True


def _ships_needed(source, target):
    needed = int(target[SHIPS]) + 1
    if target[OWNER] != -1:
        turns = _distance(source, target) / _fleet_speed(max(needed, 1))
        needed += int(turns * target[PRODUCTION]) + 3
    return needed


def _target_score(source, target, player, step):
    dist = max(_distance(source, target), 1.0)
    static_bonus = 18.0 if _is_static(target) else -8.0
    neutral_bonus = 22.0 if target[OWNER] == -1 else 0.0
    enemy_bonus = 16.0 if target[OWNER] not in (-1, player) and step > 80 else -6.0
    value = target[PRODUCTION] * 45.0 + static_bonus + neutral_bonus + enemy_bonus
    cost = target[SHIPS] * 1.25 + dist * 1.15
    return value - cost


def agent(obs):
    player = _get(obs, "player", 0)
    planets = _get(obs, "planets", []) or []
    step = int(_get(obs, "step", 0) or 0)

    my_planets = [p for p in planets if p[OWNER] == player]
    if not my_planets:
        return []

    targets = [p for p in planets if p[OWNER] != player]
    if not targets:
        return []

    moves = []
    targeted = set()

    for source in sorted(my_planets, key=lambda p: p[SHIPS], reverse=True):
        available = int(source[SHIPS])
        reserve = max(12 if len(my_planets) == 1 else 8, int(source[PRODUCTION] * 5))
        if available <= reserve + 3:
            continue

        candidates = [
            t
            for t in targets
            if t[ID] not in targeted and _path_clear(source, t, planets)
        ]
        if not candidates:
            candidates = [t for t in targets if _path_clear(source, t, planets)]
        if not candidates:
            continue

        if step < 120:
            neutral = [t for t in candidates if t[OWNER] == -1]
            if neutral:
                candidates = neutral

        target = max(candidates, key=lambda t: _target_score(source, t, player, step))
        needed = _ships_needed(source, target)
        max_send = available - reserve
        if needed > max_send:
            continue

        buffer = 2 if target[OWNER] == -1 else 5
        send = min(max_send, needed + buffer)

        if send <= 0:
            continue

        angle = math.atan2(target[Y] - source[Y], target[X] - source[X])
        moves.append([int(source[ID]), float(angle), int(send)])
        targeted.add(target[ID])

    return moves
