import pygame, random, sys
from collections import deque
pygame.init()

CELL=28
COLS=19
ROWS=21
W=COLS*CELL
H=ROWS*CELL+60
screen=pygame.display.set_mode((W,H))
pygame.display.set_caption("PACMAN - IA REAL + NIVELES")
clock=pygame.time.Clock()

BLACK=(0,0,0)
BLUE=(25,25,220)
YELLOW=(255,255,0)
WHITE=(255,255,255)
RED=(255,0,0)
PINK=(255,184,255)
CYAN=(0,255,255)
ORANGE=(255,184,0)
SCARED_BLUE=(0,0,180)

GAME_SPEED = 8
level = 1
score = 0
game_over = False
win_level = False

# --- MAPAS POR NIVEL ---
def generate_maze(lvl):
    maze=[[1]*COLS for _ in range(ROWS)]
    for r in range(1, ROWS-1):
        for c in range(1, COLS-1):
            maze[r][c]=0
    maze[10][0]=0
    maze[10][COLS-1]=0
    
    if lvl==1: # Facil - pocas paredes
        for r in [2,4,6,14,16,18]:
            maze[r][5]=1
            maze[r][13]=1
        for c in range(4,15):
            if c!=9:
                maze[5][c]=1
                maze[15][c]=1
                
    elif lvl==2: # Medio - mas paredes
        for r in [2,3,4,6,7,8,12,13,14,16,17,18]:
            maze[r][5]=1
            maze[r][9]=1
            maze[r][13]=1
        for c in range(2,17,2):
            maze[5][c]=1
            maze[15][c]=1
        maze[10][9]=1
        
    else: # Dificil - laberinto cerrado
        for r in range(2, ROWS-2, 2):
            for c in range(2, COLS-2, 2):
                if random.random()<0.5:
                    maze[r][c]=1
        for r in range(1, ROWS-1):
            maze[r][9]=0 # deja camino central
        maze[10][0]=0
        maze[10][COLS-1]=0
        for c in range(COLS):
            maze[10][c]=0 if c%2==0 else maze[10][c]
            
    # asegurar que no queden paredes en spawn
    for r in range(8,12):
        for c in range(7,12):
            maze[r][c]=0
    return maze

def can_move(x,y,maze):
    if y<0 or y>=ROWS or x<0 or x>=COLS:
        if y==10 and (x<0 or x>=COLS): return True
        return False
    return maze[y][x]!=1

# BFS para encontrar el mejor movimiento hacia el objetivo
def bfs_next_move(sx, sy, tx, ty, maze):
    if sx==tx and sy==ty:
        return None
    queue=deque()
    queue.append((sx,sy,[]))
    visited=set()
    visited.add((sx,sy))
    
    # Limitar busqueda para que no se cuelgue
    max_steps=80
    steps=0
    
    while queue and steps<max_steps:
        x,y,path=queue.popleft()
        steps+=1
        for d,(dx,dy) in enumerate([(1,0),(-1,0),(0,-1),(0,1)]):
            nx,ny=x+dx,y+dy
            if ny==10 and nx<0: nx=COLS-1
            if ny==10 and nx>=COLS: nx=0
            if (nx,ny) in visited: continue
            if not can_move(nx,ny,maze): continue
            
            new_path=path+[d]
            if nx==tx and ny==ty:
                return new_path[0]
            visited.add((nx,ny))
            queue.append((nx,ny,new_path))
    
    # si no encuentra camino, devuelve direccion aleatoria valida
    valid=[]
    for d,(dx,dy) in enumerate([(1,0),(-1,0),(0,-1),(0,1)]):
        nx,ny=sx+dx,sy+dy
        if can_move(nx,ny,maze):
            valid.append(d)
    return random.choice(valid) if valid else None

MAZE=generate_maze(level)
dots=[[0 if MAZE[r][c]==0 else 1 for c in range(COLS)] for r in range(ROWS)]
for pos in [(1,1),(1,COLS-2),(ROWS-2,1),(ROWS-2,COLS-2)]:
    dots[pos[0]][pos[1]]=3

pac_x,pac_y=9,15
pac_dir=0
next_dir=0
pac_mouth=0
pac_opening=True

# Fantasmas con personalidad real
ghosts=[
    {"x":9,"y":9,"dir":0,"color":RED,"scared":0,"name":"BLINKY"}, # Perseguidor directo
    {"x":8,"y":9,"dir":2,"color":PINK,"scared":0,"name":"PINKY"}, # Emboscador 4 adelante
    {"x":10,"y":9,"dir":1,"color":CYAN,"scared":0,"name":"INKY"}, # Impredecible
    {"x":9,"y":10,"dir":3,"color":ORANGE,"scared":0,"name":"CLYDE"}, # Aleatorio / tonto
]

ghost_move_counter=0

def get_ghost_target(g, pac_x, pac_y, pac_dir, blinky_pos):
    # Posicion 4 adelante de pacman
    ahead_x, ahead_y = pac_x, pac_y
    if pac_dir==0: ahead_x+=4
    elif pac_dir==1: ahead_x-=4
    elif pac_dir==2: ahead_y-=4
    else: ahead_y+=4
    
    ahead_x = max(1, min(COLS-2, ahead_x))
    ahead_y = max(1, min(ROWS-2, ahead_y))
    
    if g["name"]=="BLINKY":
        return pac_x, pac_y # Persigue directo
    
    elif g["name"]=="PINKY":
        return ahead_x, ahead_y # 4 casillas adelante
        
    elif g["name"]=="INKY":
        # Mitad entre Blinky y el punto adelantado + random
        bx,by=blinky_pos
        tx = ahead_x*2 - bx + random.randint(-2,2)
        ty = ahead_y*2 - by + random.randint(-2,2)
        return max(1,min(COLS-2,tx)), max(1,min(ROWS-2,ty))
        
    else: # CLYDE
        dist = abs(g["x"]-pac_x)+abs(g["y"]-pac_y)
        if dist>8:
            return pac_x, pac_y
        else:
            return 1, ROWS-2 # Se va a esquina cuando esta cerca

while True:
    clock.tick(GAME_SPEED)
    for e in pygame.event.get():
        if e.type==pygame.QUIT:
            pygame.quit()
            sys.exit()
        if e.type==pygame.KEYDOWN:
            if e.key in (pygame.K_LEFT, pygame.K_a): next_dir=1
            if e.key in (pygame.K_RIGHT, pygame.K_d): next_dir=0
            if e.key in (pygame.K_UP, pygame.K_w): next_dir=2
            if e.key in (pygame.K_DOWN, pygame.K_s): next_dir=3
            if e.key==pygame.K_r and (game_over or win_level):
                if game_over:
                    level=1
                    score=0
                MAZE=generate_maze(level)
                dots=[[0 if MAZE[r][c]==0 else 1 for c in range(COLS)] for r in range(ROWS)]
                for pos in [(1,1),(1,COLS-2),(ROWS-2,1),(ROWS-2,COLS-2)]:
                    dots[pos[0]][pos[1]]=3
                pac_x,pac_y=9,15
                pac_dir=0
                next_dir=0
                for i,g in enumerate(ghosts):
                    g["x"],g["y"]=[(9,9),(8,9),(10,9),(9,10)][i]
                    g["scared"]=0
                game_over=False
                win_level=False

    if not game_over and not win_level:
        if pac_opening:
            pac_mouth+=1
            if pac_mouth>8: pac_opening=False
        else:
            pac_mouth-=1
            if pac_mouth<0: pac_opening=True

        # Pacman
        nx,ny=pac_x,pac_y
        if next_dir==0: nx+=1
        elif next_dir==1: nx-=1
        elif next_dir==2: ny-=1
        else: ny+=1
        if ny==10 and nx<0: nx=COLS-1
        if ny==10 and nx>=COLS: nx=0
        if can_move(nx,ny,MAZE): pac_dir=next_dir

        mx,my=pac_x,pac_y
        if pac_dir==0: mx+=1
        elif pac_dir==1: mx-=1
        elif pac_dir==2: my-=1
        else: my+=1
        if my==10 and mx<0: mx=COLS-1
        if my==10 and mx>=COLS: mx=0
        if can_move(mx,my,MAZE):
            pac_x,pac_y=mx,my
            if dots[pac_y][pac_x]==0:
                dots[pac_y][pac_x]=2
                score+=10
            elif dots[pac_y][pac_x]==3:
                dots[pac_y][pac_x]=2
                score+=50
                for g in ghosts: g["scared"]=300 if level==1 else 200 if level==2 else 120

        # Fantasmas con IA real
        ghost_move_counter+=1
        # Dificultad: entre mas nivel, mas rapido se mueven
        move_every = 2 if level==1 else 1 if level==2 else 1
        if ghost_move_counter % move_every ==0:
            blinky_pos = (ghosts[0]["x"], ghosts[0]["y"])
            for g in ghosts:
                if g["scared"]>0: 
                    g["scared"]-=1
                    # Huir
                    # Busca la esquina mas lejana a pacman
                    target = (1,1) if pac_x>COLS//2 else (COLS-2, ROWS-2)
                else:
                    target = get_ghost_target(g, pac_x, pac_y, pac_dir, blinky_pos)
                
                best_dir = bfs_next_move(g["x"], g["y"], target[0], target[1], MAZE)
                if best_dir is not None:
                    g["dir"]=best_dir
                    nx,ny=g["x"],g["y"]
                    if best_dir==0: nx+=1
                    elif best_dir==1: nx-=1
                    elif best_dir==2: ny-=1
                    else: ny+=1
                    if ny==10 and nx<0: nx=COLS-1
                    if ny==10 and nx>=COLS: nx=0
                    if can_move(nx,ny,MAZE):
                        g["x"],g["y"]=nx,ny

        # COLISION = GAME OVER INSTANTANEO
        for g in ghosts:
            if abs(pac_x-g["x"])<0.8 and abs(pac_y-g["y"])<0.8:
                if g["scared"]>0:
                    g["x"],g["y"]=9,9
                    g["scared"]=0
                    score+=200
                else:
                    game_over=True # Ya no hay vidas, directo a game over
                    break

        # NIVEL COMPLETADO
        remaining = sum(1 for r in range(ROWS) for c in range(COLS) if dots[r][c]==0 or dots[r][c]==3)
        if remaining==0:
            level+=1
            if level>3: level=1 # reinicia ciclo
            win_level=True
            GAME_SPEED = min(12, 7+level) # cada nivel mas rapido

    screen.fill(BLACK)
    font=pygame.font.SysFont("Arial", 16, bold=True)
    screen.blit(font.render(f"NIVEL {level}  SCORE {score}  {'ASUSTADOS!' if any(g['scared']>0 for g in ghosts) else ''}", True, WHITE), (5,5))
    screen.blit(font.render(f"WASD - R=Reiniciar", True, (100,100,100)), (5,25))

    for r in range(ROWS):
        for c in range(COLS):
            x=c*CELL
            y=r*CELL+60
            if MAZE[r][c]==1:
                pygame.draw.rect(screen, BLUE, (x,y,CELL,CELL))
                pygame.draw.rect(screen, (0,0,120), (x+2,y+2,CELL-4,CELL-4))
            elif dots[r][c]==0:
                pygame.draw.circle(screen, WHITE, (x+CELL//2, y+CELL//2), 3)
            elif dots[r][c]==3:
                pygame.draw.circle(screen, WHITE, (x+CELL//2, y+CELL//2), 7)

    px=pac_x*CELL+CELL//2
    py=pac_y*CELL+60+CELL//2
    pygame.draw.circle(screen, YELLOW, (px,py), 11)
    if not game_over:
        ms=pac_mouth
        if pac_dir==0: pygame.draw.polygon(screen, BLACK, [(px,py),(px+12,py-ms),(px+12,py+ms)])
        elif pac_dir==1: pygame.draw.polygon(screen, BLACK, [(px,py),(px-12,py-ms),(px-12,py+ms)])
        elif pac_dir==2: pygame.draw.polygon(screen, BLACK, [(px,py),(px-ms,py-12),(px+ms,py-12)])
        else: pygame.draw.polygon(screen, BLACK, [(px,py),(px-ms,py+12),(px+ms,py+12)])

    for g in ghosts:
        gx=g["x"]*CELL+CELL//2
        gy=g["y"]*CELL+60+CELL//2
        if g["scared"]>0:
            col=SCARED_BLUE if g["scared"]>60 else WHITE
        else:
            col=g["color"]
        pygame.draw.circle(screen, col, (gx,gy-2), 10)
        pygame.draw.rect(screen, col, (gx-10,gy-2,20,9))
        # ojos
        pygame.draw.circle(screen, WHITE, (gx-4,gy-4), 3)
        pygame.draw.circle(screen, WHITE, (gx+4,gy-4), 3)
        pygame.draw.circle(screen, BLACK, (gx-4,gy-4), 1)
        pygame.draw.circle(screen, BLACK, (gx+4,gy-4), 1)

    if game_over:
        fb=pygame.font.SysFont("Arial", 32, bold=True)
        t=fb.render(f"GAME OVER - Nivel {level} - R", True, RED)
        screen.blit(t, (W//2-t.get_width()//2, H//2))
    if win_level:
        fb=pygame.font.SysFont("Arial", 28, bold=True)
        t=fb.render(f"NIVEL {level-1} COMPLETADO! R para nivel {level}", True, YELLOW)
        screen.blit(t, (W//2-t.get_width()//2, H//2))

    pygame.display.flip()