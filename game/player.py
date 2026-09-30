import pygame

SPEED=4
LANE_W=80

class Player:
    def __init__(self, x, y):
        self.rect=pygame.Rect(x-20,y-30,40,60)
        self.color=(60,160,220)
        self.move_cooldown=0

    def move(self, keys, min_x, max_x, max_y):
        # cooldown only limits lane changes, forward/back stays responsive
        if self.move_cooldown>0:
            self.move_cooldown-=1
        dx=dy=0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: dx=-LANE_W
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx=LANE_W
        if keys[pygame.K_UP] or keys[pygame.K_w]: dy=-8
        if keys[pygame.K_DOWN] or keys[pygame.K_s]: dy=8
        if dx and self.move_cooldown==0:
            self.rect.x=max(min_x,min(max_x-self.rect.width,self.rect.x+dx))
            self.move_cooldown=12
        if dy:
            # clamp both ends (the old code let the player walk off the bottom)
            self.rect.y=max(0,min(max_y-self.rect.height,self.rect.y+dy))

    def snap_to_lane(self, lanes):
        lane=round((self.rect.centerx-LANE_W/2)/LANE_W)
        lane=max(0,min(lanes-1,lane))
        self.rect.centerx=lane*LANE_W+LANE_W//2

    def draw(self,screen):
        # car body
        pygame.draw.rect(screen,self.color,self.rect,border_radius=8)
        # windows
        pygame.draw.rect(screen,(180,220,240),pygame.Rect(self.rect.x+6,self.rect.y+8,28,18),border_radius=4)
        # wheels
        for wx in [self.rect.x+4,self.rect.right-12]:
            for wy in [self.rect.y+4,self.rect.bottom-14]:
                pygame.draw.rect(screen,(30,30,30),pygame.Rect(wx,wy,8,10),border_radius=3)