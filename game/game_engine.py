import json
import os
import random
import pygame
from game.player import Player,LANE_W
from game.traffic import make_car,Log,LOG_SPEED,LOG_SPACING

LANES=8
WIDTH=LANES*LANE_W
HEIGHT=600
FPS=60
BG=(60,60,60)

# Layout, top to bottom: finish bank | river | safe bank | road
RIVER_TOP=100
RIVER_BOTTOM=180
RIVER_H=RIVER_BOTTOM-RIVER_TOP
ROAD_TOP=220
ROAD_RECT=pygame.Rect(0,ROAD_TOP,WIDTH,HEIGHT-ROAD_TOP)
NUM_LOGS=3
LOG_CYCLE=NUM_LOGS*LOG_SPACING

START_X=(LANES//2)*LANE_W+LANE_W//2   # centre of a lane (old start straddled two)
START_Y=HEIGHT-80

MAX_LIVES=3
INVULN_FRAMES=90            # 1.5s of protection after respawn
CYCLE_FRAMES=30*FPS         # day <-> night every 30s
NIGHT_BEAM=180

WIN_BONUS=500               # points awarded for reaching the top

MAX_SCORES=5
SCORE_FILE=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"highscores.json")

def load_scores():
    try:
        with open(SCORE_FILE) as f:
            return sorted((int(s) for s in json.load(f)),reverse=True)[:MAX_SCORES]
    except (OSError,ValueError,TypeError):
        return []

def save_scores(scores):
    try:
        with open(SCORE_FILE,"w") as f:
            json.dump(scores,f)
    except OSError:
        pass

class GameEngine:
    def __init__(self):
        pygame.init()
        self.screen=pygame.display.set_mode((WIDTH,HEIGHT))
        pygame.display.set_caption("Traffic Escape")
        self.clock=pygame.time.Clock()
        self.font=pygame.font.SysFont("monospace",24,bold=True)
        self.hud_font=pygame.font.SysFont("monospace",18,bold=True)
        self.big_font=pygame.font.SysFont("monospace",44,bold=True)
        self.dark=pygame.Surface((WIDTH,HEIGHT),pygame.SRCALPHA)
        self.highscores=load_scores()
        self.reset()

    def reset(self):
        self.player=Player(START_X,START_Y)
        self.cars=[]
        self.logs=[Log(i*LOG_SPACING-100,RIVER_TOP,RIVER_H) for i in range(NUM_LOGS)]
        self.timer=0
        self.frame=0
        self.spawn_interval=50
        self.speed=3
        self.score=0
        self.lives=MAX_LIVES
        self.invuln=0
        self.night=False
        self.cycle=0
        self.new_rank=None
        self.game_over=False
        self.won=False

    def handle_events(self):
        for event in pygame.event.get():
            if event.type==pygame.QUIT: return False
            if event.type==pygame.KEYDOWN and event.key==pygame.K_r: self.reset()
        return True

    # ---- lives / scores ----
    def lose_life(self):
        self.lives-=1
        if self.lives<=0:
            self.game_over=True
            self.record_score()
        else:
            self.player=Player(START_X,START_Y)
            self.invuln=INVULN_FRAMES

    def record_score(self):
        s=self.score//10
        if s<=0: return
        board=sorted(self.highscores+[s],reverse=True)[:MAX_SCORES]
        if s in board: self.new_rank=board.index(s)
        self.highscores=board
        save_scores(board)

    # ---- river ----
    def _on_log(self):
        cx=self.player.rect.centerx
        return any(l.rect.left<=cx<l.rect.right for l in self.logs)

    def update(self):
        if self.game_over or self.won: return
        self.frame+=1
        keys=pygame.key.get_pressed()
        p=self.player
        p.move(keys,0,WIDTH,HEIGHT)

        # day / night
        self.cycle+=1
        if self.cycle>=CYCLE_FRAMES:
            self.night=not self.night
            self.cycle=0

        # river: must be on a log while in the water band
        on_log=self._on_log()
        for l in self.logs:
            l.update(LOG_CYCLE,WIDTH)
        if RIVER_TOP<=p.rect.centery<RIVER_BOTTOM:
            if on_log: p.rect.x+=LOG_SPEED
            if not on_log or p.rect.left<0 or p.rect.right>WIDTH:
                self.lose_life()
                return
        elif p.rect.centery>=RIVER_BOTTOM:
            p.snap_to_lane(LANES)   # undo any drift from riding a log

        # traffic
        self.timer+=1
        if self.timer>=self.spawn_interval:
            lane=random.randint(0,LANES-1)
            self.cars.append(make_car(lane,HEIGHT,self.speed,ROAD_TOP))
            self.timer=0
            self.spawn_interval=max(22,self.spawn_interval-0.2)
        if self.invuln>0: self.invuln-=1
        hit=False
        for c in self.cars:
            c.update()
            # only the part of the car on the road counts
            if self.invuln==0 and c.rect.clip(ROAD_RECT).colliderect(p.rect):
                hit=True
        self.cars=[c for c in self.cars if not c.off_screen(HEIGHT,ROAD_TOP)]
        if hit:
            self.lose_life()
            return

        self.score+=1
        if self.score%300==0: self.speed=min(10,self.speed+0.5)
        if p.rect.top<=10:
            self.won=True
            self.score+=WIN_BONUS*10   # score is stored x10 (HUD shows score//10)
            self.record_score()

    # ---- drawing ----
    def _draw_river(self):
        pygame.draw.rect(self.screen,(40,100,180),pygame.Rect(0,RIVER_TOP,WIDTH,RIVER_H))
        off=(self.frame//2)%60
        for y in (RIVER_TOP+18,RIVER_TOP+40,RIVER_TOP+62):
            for x in range(-60,WIDTH,60):
                pygame.draw.line(self.screen,(90,150,220),(x+off,y),(x+off+20,y),2)
        for l in self.logs: l.draw(self.screen)

    def _draw_night(self):
        self.dark.set_clip(None)
        self.dark.fill((5,10,35,150))
        self.dark.set_clip(ROAD_RECT)
        for c in self.cars:
            # punch a lit cone into the darkness
            pygame.draw.polygon(self.dark,(255,240,170,40),c.beam(NIGHT_BEAM))
        self.screen.blit(self.dark,(0,0))

    def _heart(self,cx,cy,color):
        pygame.draw.circle(self.screen,color,(cx-4,cy-2),5)
        pygame.draw.circle(self.screen,color,(cx+4,cy-2),5)
        pygame.draw.polygon(self.screen,color,[(cx-9,cy),(cx+9,cy),(cx,cy+9)])

    def draw(self):
        self.screen.fill(BG)
        # road markings (road section only)
        for i in range(LANES+1):
            pygame.draw.line(self.screen,(100,100,100),(i*LANE_W,ROAD_TOP),(i*LANE_W,HEIGHT),2)
        for y in range(ROAD_TOP,HEIGHT,60):
            for i in range(LANES):
                pygame.draw.rect(self.screen,(200,200,100),pygame.Rect(i*LANE_W+LANE_W//2-3,y,6,30))
        # sidewalks / banks
        pygame.draw.rect(self.screen,(150,130,110),pygame.Rect(0,HEIGHT-50,WIDTH,50))
        pygame.draw.rect(self.screen,(150,130,110),pygame.Rect(0,0,WIDTH,RIVER_TOP))
        pygame.draw.rect(self.screen,(150,130,110),pygame.Rect(0,RIVER_BOTTOM,WIDTH,ROAD_TOP-RIVER_BOTTOM))
        self._draw_river()

        self.screen.set_clip(ROAD_RECT)
        for c in self.cars: c.draw(self.screen)
        self.screen.set_clip(None)

        if self.night: self._draw_night()

        self.screen.set_clip(ROAD_RECT)
        for c in self.cars: c.draw_lights(self.screen)
        self.screen.set_clip(None)

        # blink while invulnerable
        if not (self.invuln>0 and (self.invuln//6)%2==0):
            self.player.draw(self.screen)

        # HUD
        pygame.draw.rect(self.screen,(20,20,20),pygame.Rect(0,0,WIDTH,30))
        s=self.hud_font.render(f"Score: {self.score//10}",True,(220,220,220))
        self.screen.blit(s,(6,6))
        for i in range(MAX_LIVES):
            self._heart(170+i*26,10,(220,60,60) if i<self.lives else (70,70,70))
        g=self.hud_font.render("Goal: reach the top!",True,(220,220,220))
        self.screen.blit(g,(260,6))
        secs=(CYCLE_FRAMES-self.cycle)//FPS+1
        ph=self.hud_font.render(f"{'NIGHT' if self.night else 'DAY'} {secs}s",True,(240,220,120) if not self.night else (150,170,255))
        self.screen.blit(ph,(WIDTH-ph.get_width()-6,6))

        if self.game_over:
            self._msg("GAME OVER",(220,60,60))
        if self.won:
            self._msg("YOU MADE IT!",(80,220,80))
        pygame.display.flip()

    def _msg(self,text,color):
        ov=pygame.Surface((WIDTH,HEIGHT),pygame.SRCALPHA)
        ov.fill((0,0,0,190))
        self.screen.blit(ov,(0,0))
        def center(surf,y): self.screen.blit(surf,(WIDTH//2-surf.get_width()//2,y))
        center(self.big_font.render(text,True,color),90)
        center(self.font.render(f"Score: {self.score//10}",True,(220,220,220)),150)
        center(self.font.render("HIGH SCORES",True,(240,220,120)),200)
        for i in range(MAX_SCORES):
            val=f"{self.highscores[i]:>5}" if i<len(self.highscores) else "    -"
            col=(255,255,120) if i==self.new_rank else (200,200,200)
            center(self.font.render(f"{i+1}. {val}",True,col),240+i*32)
        center(self.font.render("Press R to Restart",True,(200,200,200)),440)

    def run(self):
        running=True
        while running:
            running=self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        pygame.quit()