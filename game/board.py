import random
import time
import math
import pygame

GRID_SIZE = 8
TILE_SIZE = 60
GEM_COLORS = [
    (220, 50, 50),   # Red
    (50, 200, 50),   # Green
    (50, 100, 240),  # Blue
    (240, 200, 40),  # Yellow
    (180, 50, 220),  # Purple
    (240, 130, 40),  # Orange
]


class Gem:

    def __init__(self, color, target_row, col, is_special=False, special_type=None):
        self.color = color
        self.target_row = target_row
        self.col = col
        self.current_y = (target_row - 2) * TILE_SIZE
        self.target_y = target_row * TILE_SIZE
        self.fall_speed = 12.0
        self.is_special = is_special      # Task 3: Special Line-Clear Gem
        self.special_type = special_type  # 'row' or 'col' line clear

    def update(self):
        if self.current_y < self.target_y:
            self.current_y += self.fall_speed
            if self.current_y > self.target_y:
                self.current_y = self.target_y

    def is_animating(self):
        return self.current_y < self.target_y


class Board:

    def __init__(self, offset_x, offset_y, target_score=500, max_moves=20):
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.target_score = target_score
        self.max_moves = max_moves
        self.grid = [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.selected = None
        self.score = 0
        self.moves_remaining = max_moves
        self.last_input_time = time.time()  # Task 4: Idle hint timer
        self.hint_pair = None                # Task 4: Idle hint pair ((r1, c1), (r2, c2))
        self.reset()

    def reset(self):
        self.score = 0
        self.moves_remaining = self.max_moves
        self.selected = None
        self.last_input_time = time.time()
        self.hint_pair = None
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                color = random.choice(GEM_COLORS)
                gem = Gem(color, r, c)
                gem.current_y = gem.target_y
                self.grid[r][c] = gem

        self.resolve_matches_initial()

    def reset_idle_timer(self):
        self.last_input_time = time.time()
        self.hint_pair = None

    def is_animating(self):
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                if self.grid[r][c] and self.grid[r][c].is_animating():
                    return True
        return False

    def swap_gems(self, pos1, pos2):
        r1, c1 = pos1
        r2, c2 = pos2

        g1, g2 = self.grid[r1][c1], self.grid[r2][c2]
        self.grid[r1][c1], self.grid[r2][c2] = g2, g1

        if self.grid[r1][c1]:
            self.grid[r1][c1].target_row = r1
            self.grid[r1][c1].target_y = r1 * TILE_SIZE
            self.grid[r1][c1].current_y = r1 * TILE_SIZE

        if self.grid[r2][c2]:
            self.grid[r2][c2].target_row = r2
            self.grid[r2][c2].target_y = r2 * TILE_SIZE
            self.grid[r2][c2].current_y = r2 * TILE_SIZE

    def is_adjacent(self, pos1, pos2):
        r1, c1 = pos1
        r2, c2 = pos2
        return abs(r1 - r2) + abs(c1 - c2) == 1

    def find_match_groups(self):
        """Finds horizontal and vertical match sequences with their lengths and gem positions."""
        horizontal_groups = []
        vertical_groups = []

        for r in range(GRID_SIZE):
            c = 0
            while c < GRID_SIZE:
                if self.grid[r][c] is None:
                    c += 1
                    continue
                match_color = self.grid[r][c].color
                start_c = c
                while c < GRID_SIZE and self.grid[r][c] and self.grid[r][c].color == match_color:
                    c += 1
                length = c - start_c
                if length >= 3:
                    horizontal_groups.append({
                        'dir': 'h',
                        'row': r,
                        'cols': list(range(start_c, c)),
                        'length': length,
                        'positions': [(r, col) for col in range(start_c, c)]
                    })

        for c in range(GRID_SIZE):
            r = 0
            while r < GRID_SIZE:
                if self.grid[r][c] is None:
                    r += 1
                    continue
                match_color = self.grid[r][c].color
                start_r = r
                while r < GRID_SIZE and self.grid[r][c] and self.grid[r][c].color == match_color:
                    r += 1
                length = r - start_r
                if length >= 3:
                    vertical_groups.append({
                        'dir': 'v',
                        'col': c,
                        'rows': list(range(start_r, r)),
                        'length': length,
                        'positions': [(row, c) for row in range(start_r, r)]
                    })

        return horizontal_groups, vertical_groups

    def find_matches(self):
        matched = set()
        h_groups, v_groups = self.find_match_groups()
        for g in h_groups:
            matched.update(g['positions'])
        for g in v_groups:
            matched.update(g['positions'])
        return matched

    def drop_and_refill(self):
        for c in range(GRID_SIZE):
            empty_slots = 0
            for r in range(GRID_SIZE - 1, -1, -1):
                if self.grid[r][c] is None:
                    empty_slots += 1
                elif empty_slots > 0:
                    gem = self.grid[r][c]
                    gem.target_row = r + empty_slots
                    gem.target_y = (r + empty_slots) * TILE_SIZE
                    self.grid[r + empty_slots][c] = gem
                    self.grid[r][c] = None

            for r in range(empty_slots):
                color = random.choice(GEM_COLORS)
                gem = Gem(color, r, c)
                gem.current_y = -((empty_slots - r) * TILE_SIZE)
                self.grid[r][c] = gem

    def resolve_matches_initial(self):
        """Initial board cleanup without scoring or special gem generation."""
        while True:
            matches = self.find_matches()
            if not matches:
                break
            for r, c in matches:
                self.grid[r][c] = None
            self.drop_and_refill()

    def resolve_matches_cascade(self, swap_pos1=None, swap_pos2=None):
        """
        Resolves matches with Task 2 (Cascade Multiplier) and Task 3 (Special 4-in-a-row gems & line detonation).
        """
        total_score_gained = 0
        cascade_step = 1

        while True:
            h_groups, v_groups = self.find_match_groups()
            if not h_groups and not v_groups:
                break

            matched_positions = set()
            special_creations = []

            all_groups = h_groups + v_groups
            for g in all_groups:
                matched_positions.update(g['positions'])
                # Task 3: 4-in-a-row creates a special line-clear gem
                if g['length'] >= 4:
                    # Choose location for special gem (preferably one of swapped positions, else middle)
                    spawn_pos = None
                    if swap_pos1 in g['positions']:
                        spawn_pos = swap_pos1
                    elif swap_pos2 in g['positions']:
                        spawn_pos = swap_pos2
                    else:
                        spawn_pos = g['positions'][len(g['positions']) // 2]
                    
                    special_type = 'row' if g['dir'] == 'h' else 'col'
                    sample_gem = self.grid[spawn_pos[0]][spawn_pos[1]]
                    color = sample_gem.color if sample_gem else random.choice(GEM_COLORS)
                    special_creations.append((spawn_pos, color, special_type))

            # Task 3: If any matched gem is special, add its entire row or column to cleared positions
            line_clear_positions = set()
            for r, c in matched_positions:
                gem = self.grid[r][c]
                if gem and gem.is_special:
                    if gem.special_type == 'row':
                        for col in range(GRID_SIZE):
                            line_clear_positions.add((r, col))
                    elif gem.special_type == 'col':
                        for row in range(GRID_SIZE):
                            line_clear_positions.add((row, c))

            all_cleared = matched_positions.union(line_clear_positions)
            
            # Task 2: Points with cascade combo multiplier
            gems_cleared_count = len(all_cleared)
            total_score_gained += gems_cleared_count * 10 * cascade_step

            # Remove cleared gems
            for r, c in all_cleared:
                self.grid[r][c] = None

            # Spawn created special gems at their designated positions
            for (r, c), color, stype in special_creations:
                special_gem = Gem(color, r, c, is_special=True, special_type=stype)
                special_gem.current_y = r * TILE_SIZE
                self.grid[r][c] = special_gem

            self.drop_and_refill()
            cascade_step += 1

        self.score += total_score_gained
        return total_score_gained > 0

    def process_swap(self, pos1, pos2):
        if not self.is_adjacent(pos1, pos2) or self.is_game_over() or self.is_animating():
            return False

        self.reset_idle_timer()

        self.swap_gems(pos1, pos2)
        matches = self.find_matches()

        # Task 1: Check if swap creates at least one valid match
        if not matches:
            # Revert swap, DO NOT deduct move
            self.swap_gems(pos1, pos2)
            return False

        # Valid swap: Deduct 1 move
        self.moves_remaining -= 1

        # Resolve matches with cascade combo multiplier & special gem logic
        self.resolve_matches_cascade(swap_pos1=pos1, swap_pos2=pos2)
        return True

    def find_possible_swap(self):
        """Task 4: Searches for a valid adjacent swap that forms a match."""
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                for dr, dc in [(0, 1), (1, 0)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < GRID_SIZE and 0 <= nc < GRID_SIZE:
                        # Simulate swap
                        self.swap_gems((r, c), (nr, nc))
                        matches = self.find_matches()
                        self.swap_gems((r, c), (nr, nc))  # Revert
                        if matches:
                            return ((r, c), (nr, nc))
        return None

    def is_game_over(self):
        return self.score >= self.target_score or self.moves_remaining <= 0

    def check_result(self):
        if self.score >= self.target_score:
            return "WIN"
        if self.moves_remaining <= 0:
            return "LOSS"
        return None

    def update(self):
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                if self.grid[r][c]:
                    self.grid[r][c].update()

        # Task 4: Idle hint timer update (5 seconds threshold)
        if not self.is_animating() and not self.is_game_over():
            if time.time() - self.last_input_time > 5.0:
                if self.hint_pair is None:
                    self.hint_pair = self.find_possible_swap()
            else:
                self.hint_pair = None
        else:
            self.hint_pair = None

    def render(self, surface):
        board_rect = pygame.Rect(
            self.offset_x, self.offset_y, GRID_SIZE * TILE_SIZE, GRID_SIZE * TILE_SIZE
        )
        pygame.draw.rect(surface, (20, 22, 28), board_rect, border_radius=8)
        pygame.draw.rect(surface, (60, 65, 75), board_rect, width=3, border_radius=8)

        # Task 4: Calculate pulse alpha/width for idle hint animation
        hint_pulse = (math.sin(time.time() * 6) + 1) / 2  # 0.0 to 1.0

        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                gem = self.grid[r][c]
                if gem:
                    x = self.offset_x + c * TILE_SIZE
                    y = self.offset_y + gem.current_y
                    tile_rect = pygame.Rect(x + 2, y + 2, TILE_SIZE - 4, TILE_SIZE - 4)

                    pygame.draw.rect(surface, gem.color, tile_rect, border_radius=10)
                    pygame.draw.rect(
                        surface, (255, 255, 255), tile_rect, width=1, border_radius=10
                    )

                    # Task 3: Render visual indicator for Special Line-Clear Gem
                    if gem.is_special:
                        glow_color = (255, 255, 255)
                        # Inner glowing circle
                        pygame.draw.circle(
                            surface, glow_color, tile_rect.center, TILE_SIZE // 4, width=3
                        )
                        # Line direction indicator
                        if gem.special_type == 'row':
                            pygame.draw.line(
                                surface, glow_color,
                                (tile_rect.left + 8, tile_rect.centery),
                                (tile_rect.right - 8, tile_rect.centery), width=3
                            )
                        else:
                            pygame.draw.line(
                                surface, glow_color,
                                (tile_rect.centerx, tile_rect.top + 8),
                                (tile_rect.centerx, tile_rect.bottom - 8), width=3
                            )

                if self.selected == (r, c):
                    sel_x = self.offset_x + c * TILE_SIZE
                    sel_y = self.offset_y + r * TILE_SIZE
                    sel_rect = pygame.Rect(sel_x + 2, sel_y + 2, TILE_SIZE - 4, TILE_SIZE - 4)
                    pygame.draw.rect(
                        surface, (255, 255, 255), sel_rect, width=4, border_radius=10
                    )

        # Task 4: Draw pulsing idle hint highlight
        if self.hint_pair and not self.selected:
            hint_color = (255, 215, 0)  # Gold highlight
            border_w = int(2 + hint_pulse * 4)
            for (hr, hc) in self.hint_pair:
                hx = self.offset_x + hc * TILE_SIZE
                hy = self.offset_y + hr * TILE_SIZE
                h_rect = pygame.Rect(hx + 2, hy + 2, TILE_SIZE - 4, TILE_SIZE - 4)
                pygame.draw.rect(surface, hint_color, h_rect, width=border_w, border_radius=10)

