import pygame
import random

LANE_W=80
COLORS=[(220,60,60),(220,140,40),(140,60,180),(60,180,80),(180,180,40),(60,80,200)]
LOG_SPEED=2
LOG_SPACING=260

class Car:
    def __init__(self, lane_x, y, direction, speed):
        self.rect=pygame.Rect(lane_x+10,y,60,80)
        self.direction=direction  # 1=down, -1=up
        self.speed=speed
        self.color=random.choice(COLORS)

    def update(self):
        self.rect.y+=self.direction*self.speed

    def off_screen(self,height,top=0):
        return self.rect.top>height+100 or self.rect.bottom<top-100

    def front_y(self):
        return self.rect.bottom if self.direction==1 else self.rect.top

    def beam(self,length):
        # light cone in front of the car
        fy=self.front_y()
        end=fy+self.direction*length
        r=self.rect
        return [(r.x+6,fy),(r.right-6,fy),(r.right+14,end),(r.x-14,end)]

    def draw(self,screen):
        pygame.draw.rect(screen,self.color,self.rect,border_radius=8)
        pygame.draw.rect(screen,(180,220,240),pygame.Rect(self.rect.x+8,self.rect.y+10,44,22),border_radius=4)
        for wx in [self.rect.x+6,self.rect.right-16]:
            for wy in [self.rect.y+4,self.rect.bottom-16]:
                pygame.draw.rect(screen,(30,30,30),pygame.Rect(wx,wy,10,12),border_radius=3)

    def draw_lights(self,screen):
        ly=self.front_y()-self.direction*6
        for lx in (self.rect.x+20,self.rect.right-20):
            pygame.draw.circle(screen,(255,240,150),(lx,ly),5)

class Log:
    WIDTH=120
    def __init__(self,x,river_top,river_h,speed=LOG_SPEED):
        self.rect=pygame.Rect(x,river_top+10,self.WIDTH,river_h-20)
        self.speed=speed

    def update(self,wrap_len,screen_w):
        self.rect.x+=self.speed
        # once fully off the right edge, loop back behind the left edge
        if self.rect.left>=screen_w:
            self.rect.x-=wrap_len

    def draw(self,screen):
        pygame.draw.rect(screen,(110,70,30),self.rect,border_radius=12)
        pygame.draw.rect(screen,(150,105,55),self.rect.inflate(-10,-20),border_radius=8)
        for x in range(self.rect.x+24,self.rect.right-12,28):
            pygame.draw.line(screen,(90,55,20),(x,self.rect.y+8),(x,self.rect.bottom-8),2)

def make_car(lane_idx,height,speed,top=0):
    x=lane_idx*LANE_W
    direction=1 if lane_idx%2==0 else -1
    y=top-90 if direction==1 else height+10
    return Car(x,y,direction,speed)