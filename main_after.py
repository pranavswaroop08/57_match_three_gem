import sys
import pygame
from game.board import Board, GRID_SIZE, TILE_SIZE

SCREEN_WIDTH = 600
SCREEN_HEIGHT = 650
FPS = 60


def main():
    pygame.init()
    pygame.display.set_caption("Match-3 Gem Swap - AFTER (Fixed & Features)")
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()

    offset_x = (SCREEN_WIDTH - (GRID_SIZE * TILE_SIZE)) // 2
    offset_y = (SCREEN_HEIGHT - (GRID_SIZE * TILE_SIZE)) // 2 + 30
    board = Board(offset_x, offset_y, target_score=500, max_moves=20)

    font_big = pygame.font.SysFont(None, 48)
    font_small = pygame.font.SysFont(None, 24)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if board.is_game_over() or board.is_animating():
                    continue
                mx, my = event.pos
                bx = mx - board.offset_x
                by = my - board.offset_y
                if 0 <= bx < GRID_SIZE * TILE_SIZE and 0 <= by < GRID_SIZE * TILE_SIZE:
                    col = int(bx // TILE_SIZE)
                    row = int(by // TILE_SIZE)
                    if board.selected is None:
                        board.selected = (row, col)
                    else:
                        prev_selected = board.selected
                        if prev_selected == (row, col):
                            board.selected = None
                        else:
                            board.process_swap(prev_selected, (row, col))
                            board.selected = None
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                board.reset()

        board.update()

        screen.fill((32, 34, 40))

        title_surf = font_big.render("MATCH-3 GEM SWAP (AFTER)", True, (240, 240, 240))
        screen.blit(title_surf, (SCREEN_WIDTH // 2 - title_surf.get_width() // 2, 10))
        hud_text = (
            f"SCORE: {board.score} / {board.target_score}   |   "
            f"MOVES LEFT: {board.moves_remaining}"
        )
        hud_surf = font_small.render(hud_text, True, (80, 220, 180))
        screen.blit(hud_surf, (SCREEN_WIDTH // 2 - hud_surf.get_width() // 2, 55))

        board.render(screen)

        inst_surf = font_small.render(
            "Fixed Swap Bug, Combo Multipliers, 4-in-a-Row Gems, 5s Idle Hint!",
            True,
            (180, 180, 180),
        )
        screen.blit(
            inst_surf, (SCREEN_WIDTH // 2 - inst_surf.get_width() // 2, SCREEN_HEIGHT - 25)
        )

        result = board.check_result()
        if result:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 190))
            screen.blit(overlay, (0, 0))

            if result == "WIN":
                msg = "STAGE CLEARED!"
                color = (80, 220, 80)
            else:
                msg = "OUT OF MOVES!"
                color = (240, 80, 80)

            res_surf = font_big.render(msg, True, color)
            screen.blit(
                res_surf,
                (SCREEN_WIDTH // 2 - res_surf.get_width() // 2, SCREEN_HEIGHT // 2 - 40),
            )

            sub_text = f"Final Score: {board.score}  |  Press [R] to Play Again"
            sub_surf = font_small.render(sub_text, True, (220, 220, 220))
            screen.blit(
                sub_surf,
                (SCREEN_WIDTH // 2 - sub_surf.get_width() // 2, SCREEN_HEIGHT // 2 + 10),
            )

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
