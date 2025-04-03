#!/usr/bin/env python3

# pip install pygame
# Run this script

import pygame
import random
import sys

# --- Pygame Initialization ---
pygame.init()

# --- Constants ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 450 # Increased height for two rows + info
BACKGROUND_COLOR = (135, 206, 235) # Sky Blue
PATH_COLOR = (188, 143, 143) # Rosy Brown (slightly lighter for paths)
MANHOLE_VISUAL_COLOR = (50, 50, 50) # Dark Gray for visual circle outline
MANHOLE_OPEN_COLOR = (0, 0, 0) # Black for open hole visual
PLAYER_COLOR = (100, 100, 100) # Gray (the cover itself)
PLAYER_BORDER_COLOR = (200, 200, 200)
PEDESTRIAN_COLOR = (255, 192, 203) # Pink
PEDESTRIAN_BORDER_COLOR = (50, 50, 50)
TEXT_COLOR = (0, 0, 0) # Black
GAME_OVER_TEXT_COLOR = (255, 0, 0) # Red
RESTART_TEXT_COLOR = (200, 200, 200) # Light Gray

# --- Game Area ---
# Define Y positions for the center of each path/row of manholes
PATH_CENTERS_Y = [SCREEN_HEIGHT * 0.40, SCREEN_HEIGHT * 0.75]
PATH_VISUAL_HEIGHT = 5 # Thin line for visual path representation

# --- Manholes ---
# Define X positions for the center of manholes in each row
MANHOLE_CENTERS_X = [SCREEN_WIDTH * 0.30, SCREEN_WIDTH * 0.70]
MANHOLE_VISUAL_RADIUS = 25 # Visual radius of the circle
MANHOLE_COLLISION_WIDTH = 50 # Effective width centered on MANHOLE_CENTERS_X for collision

# --- Player (The Manhole Cover) ---
# The player's visual IS the cover, size it similarly to the manhole visual
PLAYER_WIDTH = MANHOLE_COLLISION_WIDTH + 2 # Slightly larger than hole width
PLAYER_HEIGHT = MANHOLE_VISUAL_RADIUS * 2 + 2 # Square-ish cover
player_rect = pygame.Rect(0, 0, PLAYER_WIDTH, PLAYER_HEIGHT) # Position set dynamically

# --- Pedestrians ---
PEDESTRIAN_WIDTH = 20
PEDESTRIAN_HEIGHT = 40
PEDESTRIAN_SPEED = 1.5 # Slightly faster perhaps
PEDESTRIAN_SPAWN_RATE_MIN = 200 # Can spawn faster with more holes
PEDESTRIAN_SPAWN_RATE_MAX = 400
PEDESTRIAN_Y_OFFSET = - (PEDESTRIAN_HEIGHT / 2) # Offset to make feet align with path center

# --- Fonts ---
try:
    FONT_SIZE_INFO = 36
    FONT_SIZE_GAMEOVER = 60
    FONT_SIZE_RESTART = 30
    info_font = pygame.font.Font(None, FONT_SIZE_INFO)
    game_over_font = pygame.font.Font(None, FONT_SIZE_GAMEOVER)
    restart_font = pygame.font.Font(None, FONT_SIZE_RESTART)
except Exception as e:
    print(f"Warning: Font loading failed. Using fallback. Error: {e}")
    info_font = pygame.font.SysFont(pygame.font.get_default_font(), FONT_SIZE_INFO)
    game_over_font = pygame.font.SysFont(pygame.font.get_default_font(), FONT_SIZE_GAMEOVER)
    restart_font = pygame.font.SysFont(pygame.font.get_default_font(), FONT_SIZE_RESTART)


# --- Game Variables ---
score = 0
lives = 3
# Player position tracked by row and column index
player_row_index = 0 # 0 for top row, 1 for bottom row
player_col_index = 0 # 0 for left manhole, 1 for right manhole
pedestrians = [] # List of dicts: {'rect': Rect, 'row': 0 or 1, 'scored_at_indices': set()}
game_over = False
clock = pygame.time.Clock()
spawn_timer = 0
next_spawn_delay = random.randint(PEDESTRIAN_SPAWN_RATE_MIN, PEDESTRIAN_SPAWN_RATE_MAX)


# --- Screen Setup ---
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Manhole Game")

# --- Helper Functions ---
def create_pedestrian():
    """Creates a new pedestrian rect and data dict for a random row."""
    ped_row = random.choice([0, 1]) # Assign to top (0) or bottom (1) row
    ped_center_y = PATH_CENTERS_Y[ped_row]
    # Place pedestrian so their center Y is on the path center Y
    ped_rect = pygame.Rect(
        0 - PEDESTRIAN_WIDTH, # Start off screen left
        ped_center_y - PEDESTRIAN_HEIGHT / 2, # Center vertically on the path center
        PEDESTRIAN_WIDTH,
        PEDESTRIAN_HEIGHT
    )
    return {'rect': ped_rect, 'row': ped_row, 'scored_at_indices': set()}

def draw_text(text, font, color, surface, x, y, center=False):
    """Renders and draws text. Can center horizontally."""
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect()
    if center:
        text_rect.center = (x, y)
    else:
        text_rect.topleft = (x, y)
    surface.blit(text_surface, text_rect)

def get_player_manhole_pos():
    """Calculates the center coordinates of the manhole the player is covering."""
    target_x = MANHOLE_CENTERS_X[player_col_index]
    target_y = PATH_CENTERS_Y[player_row_index]
    return target_x, target_y

def reset_game():
    """Resets game variables to start a new game."""
    global score, lives, player_row_index, player_col_index, pedestrians, game_over, spawn_timer, next_spawn_delay
    score = 0
    lives = 3
    player_row_index = 0
    player_col_index = 0
    pedestrians = []
    game_over = False
    spawn_timer = 0
    next_spawn_delay = random.randint(PEDESTRIAN_SPAWN_RATE_MIN, PEDESTRIAN_SPAWN_RATE_MAX)
    # Update player rect position based on initial index
    player_rect.center = get_player_manhole_pos()
    print("Game Reset!")


# --- Initial Setup ---
reset_game() # Initialize game state


# --- Main Game Loop ---
running = True
while running:
    # --- Event Handling ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if not game_over:
                moved = False
                if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                    player_col_index = (player_col_index - 1) % len(MANHOLE_CENTERS_X) # Cycle left
                    moved = True
                elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                    player_col_index = (player_col_index + 1) % len(MANHOLE_CENTERS_X) # Cycle right
                    moved = True
                elif event.key == pygame.K_UP or event.key == pygame.K_w:
                    player_row_index = (player_row_index - 1) % len(PATH_CENTERS_Y) # Cycle up
                    moved = True
                elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                    player_row_index = (player_row_index + 1) % len(PATH_CENTERS_Y) # Cycle down
                    moved = True

                if moved:
                    # Update player rect position
                    player_rect.center = get_player_manhole_pos()

            else: # If game over, check for restart key
                 if event.key == pygame.K_r:
                     reset_game()


    # --- Game Logic (only if not game over) ---
    if not game_over:
        # Spawn Pedestrians
        spawn_timer += 1
        if spawn_timer >= next_spawn_delay:
             pedestrians.append(create_pedestrian())
             spawn_timer = 0
             next_spawn_delay = random.randint(PEDESTRIAN_SPAWN_RATE_MIN, PEDESTRIAN_SPAWN_RATE_MAX)

        # --- Move Pedestrians & Check Collisions ---
        pedestrians_to_remove_indices = []

        for i, ped_data in enumerate(pedestrians):
            ped_rect = ped_data['rect']
            ped_row = ped_data['row']
            scored_at_indices = ped_data['scored_at_indices'] # This set stores tuples (row, col)

            # Move pedestrian
            ped_rect.x += PEDESTRIAN_SPEED
            ped_center_x = ped_rect.centerx
            fell_in_hole = False

            # Check collision with manhole columns
            for current_col_index, manhole_x in enumerate(MANHOLE_CENTERS_X):
                zone_left = manhole_x - MANHOLE_COLLISION_WIDTH / 2
                zone_right = manhole_x + MANHOLE_COLLISION_WIDTH / 2

                # Is pedestrian center within this manhole column's horizontal zone?
                if zone_left < ped_center_x < zone_right:
                    # Check if player is covering this specific manhole (matching row and column)
                    is_covered = (ped_row == player_row_index and current_col_index == player_col_index)

                    if is_covered:
                        # Player IS covering this hole - check for scoring
                        current_hole_tuple = (ped_row, current_col_index)
                        # Score only if pedestrian just passed center AND hasn't scored for this hole yet
                        if ped_center_x >= manhole_x and current_hole_tuple not in scored_at_indices:
                             score += 1
                             scored_at_indices.add(current_hole_tuple)
                             # print(f"Score! Ped {i} crossed covered hole {current_hole_tuple}") # Debug
                    else:
                        # Player is NOT covering this specific hole - FALL!
                        lives -= 1
                        print(f"Ouch! Fell in hole ({ped_row}, {current_col_index}). Lives: {lives}") # Debug
                        pedestrians_to_remove_indices.append(i)
                        fell_in_hole = True
                        break # No need to check other columns for this fallen pedestrian

            # --- Remove Pedestrians Off Screen ---
            if not fell_in_hole and ped_rect.left > SCREEN_WIDTH:
                 score += 5 # Bonus for reaching the end safely
                 pedestrians_to_remove_indices.append(i)
                 # print(f"Ped {i} (row {ped_row}) reached end safely. Score +5") # Debug

        # --- Remove fallen/off-screen pedestrians ---
        for index in sorted(list(set(pedestrians_to_remove_indices)), reverse=True):
             if 0 <= index < len(pedestrians):
                 del pedestrians[index]

        # --- Check Game Over condition ---
        if lives <= 0:
            game_over = True


    # --- Drawing ---
    # Background
    screen.fill(BACKGROUND_COLOR)

    # Draw Paths (thin lines now)
    for path_y in PATH_CENTERS_Y:
        pygame.draw.line(screen, PATH_COLOR, (0, path_y), (SCREEN_WIDTH, path_y), PATH_VISUAL_HEIGHT)

    # Draw Manholes visuals OR the Player Cover
    for r_idx, path_y in enumerate(PATH_CENTERS_Y):
        for c_idx, mh_x in enumerate(MANHOLE_CENTERS_X):
            # Check if player is covering this specific manhole
            is_player_here = (r_idx == player_row_index and c_idx == player_col_index)

            if is_player_here and not game_over:
                # Draw the player's cover instead of the manhole visual
                pygame.draw.rect(screen, PLAYER_COLOR, player_rect)
                pygame.draw.rect(screen, PLAYER_BORDER_COLOR, player_rect, 2)
            else:
                # Draw the visual for the manhole (draw outline first, then fill if open)
                pygame.draw.circle(screen, MANHOLE_VISUAL_COLOR, (mh_x, path_y), MANHOLE_VISUAL_RADIUS, 2) # Outline
                if not game_over: # Only show "open" if game is running
                    # Fill with black if player isn't here (it's open)
                     pygame.draw.circle(screen, MANHOLE_OPEN_COLOR, (mh_x, path_y), MANHOLE_VISUAL_RADIUS - 2) # Fill inside outline


    # Draw Pedestrians
    for ped_data in pedestrians:
        pygame.draw.rect(screen, PEDESTRIAN_COLOR, ped_data['rect'])
        pygame.draw.rect(screen, PEDESTRIAN_BORDER_COLOR, ped_data['rect'], 1)


    # Draw Score and Lives
    draw_text(f"Score: {score}", info_font, TEXT_COLOR, screen, 10, 10)
    draw_text(f"Lives: {lives}", info_font, TEXT_COLOR, screen, SCREEN_WIDTH - 110, 10)

    # --- Draw Game Over Screen ---
    if game_over:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))
        draw_text("GAME OVER", game_over_font, GAME_OVER_TEXT_COLOR, screen, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40, center=True)
        draw_text(f"Final Score: {score}", info_font, TEXT_COLOR, screen, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20, center=True)
        draw_text("Press 'R' to Restart", restart_font, RESTART_TEXT_COLOR, screen, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 70, center=True)


    # --- Update Display ---
    pygame.display.flip()

    # --- Frame Rate Control ---
    clock.tick(60) # Aim for 60 FPS

# --- Quit Pygame ---
print("Exiting game.")
pygame.quit()
sys.exit()
