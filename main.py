import pygame
import random

WIDTH = 1200
HEIGHT = 700
NUM_MINES = 99

# print(pygame.font.get_fonts())

# init
pygame.init()
window = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("MineSweeper")

# background color
window.fill((200, 200, 200))

# separator
pygame.draw.line(window, (0, 0, 0), (0, 640), (WIDTH, 640), 2)

mine_value = -1
empty_value = 0  

def check_surrounding(board: list[list[int]], y: int, x: int):
    """
    Checks surrounding squares for mines
    - board: 2D list that represents the board
    - y: y coordinate of square
    - x: x coordinate of square
    """
    num_mines = 0
    for i in range(-1, 2):
        for j in range(-1, 2):
            if y + i < 0 or y + i > 15 or x + j < 0 or x + j > 29:
                continue
            if board[y + i][x + j] == mine_value:
                num_mines += 1
    return num_mines       
        
def generate_mine():
    """
    Generates a random mine position
    - return: (y, x) coordinates of mine
    """
    x = random.randint(0, 29)
    y = random.randint(0, 15)
    return (y, x)

def generate_board():
    """
    Generates the board
    - return: 2D list of that represents the board
    """
    board = []
    # set all squares to empty
    for y in range(16):
        row = []
        for x in range(30):
            row.append(empty_value)
        board.append(row)
        
    # add mines
    mines = []
    for _ in range(NUM_MINES):
        y, x = generate_mine()
        while (y, x) in mines:      # if there's already a mine at x, y, generate new x, y
            y, x = generate_mine()
        mines.append((y, x))
        board[y][x] = mine_value
        
    # add numbers
    for y in range(16):
        for x in range(30):
            if board[y][x] == mine_value:
                continue
            board[y][x] = check_surrounding(board, y, x)
        
    return board

def draw_grid():
    """
    Draws a board of 30 x 16 squares
    """
    for y in range(16):
        for x in range(30):
            rect = pygame.Rect(x * 40, y * 40, 40, 40)
            pygame.draw.rect(window, (255, 255, 255), rect, 1)
            
            # use unrevealed.png for unrevealed squares
            unrevealed = pygame.image.load("assets/unrevealed.png")
            unrevealed = pygame.transform.scale(unrevealed, (40, 40))
            window.blit(unrevealed, (x * 40, y * 40))
 
def chord_from_empty(y: int, x: int, revealed: list[tuple[int, int]], board: list[list[int]]):
    """
    Reveal all surrounding squares if square is empty
    - x: x coordinate of square
    - y: y coordinate of square
    - revealed: list of revealed squares
    """
    # check surrounding squares
    for i in range(-1, 2):
        for j in range(-1, 2):
            if y + i < 0 or y + i > 15 or x + j < 0 or x + j > 29:
                continue
            if (x + j, y + i) in revealed:
                continue
            
            # reveal square
            revealed.append((x + j, y + i))
            img = pygame.image.load(f"assets/{board[y + i][x + j]}.png")
            img = pygame.transform.scale(img, (40, 40))
            
            if board[y + i][x + j] == 0 :
                window.blit(img, ((x + j) * 40, (y + i) * 40))
                
                # if square is empty, chord_from_empty
                chord_from_empty(y + i, x + j, revealed, board)
                
            elif board[y + i][x + j] != mine_value:
                window.blit(img, ((x + j) * 40, (y + i) * 40))

def chord_from_flagged(x: int, y: int, revealed: list[tuple[int, int]], flagged: list[tuple[int, int]], board: list[list[int]]):
    """
    Reveal all surrounding squares except for flagged squares
    """
    for i in range(-1, 2):
        for j in range(-1, 2):
            # out of bounds checks
            if y + i < 0 or y + i > 15 or x + j < 0 or x + j > 29:
                continue
            if (x + j, y + i) in flagged:
                continue
            
            # reveal square
            revealed.append((x + j, y + i))
            img = pygame.image.load(f"assets/{board[y + i][x + j]}.png")
            img = pygame.transform.scale(img, (40, 40))
            
            if board[y + i][x + j] == 0:
                window.blit(img, ((x + j) * 40, (y + i) * 40))
                
                # if square is empty, chord_from_empty
                chord_from_empty(y + i, x + j, revealed, board)
            
            if board[y + i][x + j] not in revealed:
                window.blit(img, ((x + j) * 40, (y + i) * 40))
                               
    pygame.display.update()

def game_over():
    """
    Game over screen
    """
    # text = pygame.font.SysFont("Arial", 50).render("Game Over", True, (255, 0, 0))
    # window.blit(text, (WIDTH // 2 + 100, 645))
    # pygame.display.update()
    
    reset_pressed = False
    while not reset_pressed:
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                if pos[0] >= WIDTH // 2 - 20 and pos[0] <= WIDTH // 2 + 20 and pos[1] >= 650 and pos[1] <= 690:
                    
                    reset_pressed = True
                    
                    reset_board()
                    
                    break
    
            if event.type == pygame.QUIT:
                pygame.quit()
                break    
    play()
    
def reset_board():
    reset_pressed = pygame.image.load("assets/reset_pressed.png")
    reset_pressed = pygame.transform.scale(reset_pressed, (40, 40))
    window.blit(reset_pressed, (WIDTH // 2 - 20, 650))
    pygame.display.update()

####################
## main game loop ##
####################
def play():
    
    # reset the reset button
    reset = pygame.image.load("assets/reset.png")
    reset = pygame.transform.scale(reset, (40, 40))
    window.blit(reset, (WIDTH // 2 - 20, 650))
    
    # generate new board and reset the grid
    board = generate_board()
    draw_grid()

    # to keep track of revealed and flagged squares
    flagged = []
    revealed = []
    
    # game loop
    running = True
    while running:
            
        for event in pygame.event.get():
            
            # check if game over
            for square in revealed:
                if board[square[1]][square[0]] == mine_value:
                    game_over()
            
            # check for user quit
            if event.type == pygame.QUIT:
                running = False
                
            # handle mouse click
            if event.type == pygame.MOUSEBUTTONDOWN:
                    
                # get x, y coordinates of clicked square
                pos = pygame.mouse.get_pos()
                
                # reset if reset button is clicked
                if pos[0] >= WIDTH // 2 - 20 and pos[0] <= WIDTH // 2 + 20 and pos[1] >= 650 and pos[1] <= 690:
                    reset_board()
                    play()
                
                # get x, y coordinates of clicked square
                x = pos[0] // 40
                y = pos[1] // 40
                
                # out of bounds check
                if y > 15 or y < 0 or x > 29 or x < 0:
                    continue
                
                # right click (flag)
                if event.button == 3:
                    # if square is unrevealed, place flag
                    if (x, y) not in revealed and (x, y) not in flagged:
                        flag = pygame.image.load("assets/flag.png")
                        flag = pygame.transform.scale(flag, (40, 40))
                        window.blit(flag, (x * 40, y * 40))
                        flagged.append((x, y))
                    # if square is flagged, remove flag
                    elif (x, y) in flagged:
                        unrevealed = pygame.image.load("assets/unrevealed.png")
                        unrevealed = pygame.transform.scale(unrevealed, (40, 40))
                        window.blit(unrevealed, (x * 40, y * 40))
                        flagged.remove((x, y))
                        
                # left click (reveal)
                elif event.button == 1:
                    # if square is flagged, do nothing
                    if (x, y) in flagged:
                        continue
                    # if square is unrevealed, reveal square
                    elif (x, y) not in revealed:
                        revealed.append((x, y))
                        img = pygame.image.load(f"assets/{board[y][x]}.png")
                        img = pygame.transform.scale(img, (40, 40))
                        window.blit(img, (x * 40, y * 40))
                        
                        # if square is empty, chord_from_empty
                        if board[y][x] == 0:
                            chord_from_empty(y, x, revealed, board)
                    # if square is already revealed, then reveal surrounding squares if current square has enough flags         
                    elif (x, y) in revealed:   
                        num_flags = 0
                        for i in range(-1, 2):
                            for j in range(-1, 2):
                                # out of bounds checks
                                if y + i < 0 or y + i > 15 or x + j < 0 or x + j > 29:
                                    continue
                                if (x + j, y + i) in flagged:
                                    num_flags += 1
                        # if enough flags, reveal all surrounding squares except for flagged squares
                        if num_flags == board[y][x]:
                            chord_from_flagged(x, y, revealed, flagged, board)
               
            # check if game is won
            if len(revealed) == 480 - NUM_MINES:
                win = pygame.image.load("assets/win.png")
                win = pygame.transform.scale(win, (40, 40))
                window.blit(win, (WIDTH // 2 - 20, 650))
                         
            # update display
            pygame.display.update()
          
play()