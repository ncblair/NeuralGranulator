
# https://stackoverflow.com/questions/28032822/how-to-insert-a-slider-in-pygame
import pygame
import sys
import math
import numpy as np

from pygame.locals import *


pygame.init()
screen = pygame.display.set_mode((800, 600))
# screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
screenColor = (255,255,255)
screen.fill(screenColor)
pygame.display.update(pygame.Rect(0,0,800,600))

class Knob :
    def __init__(self,sx,sy,width,height,bg_color,fg_color,min_val, max_val,start_val):
        self.DRAG_MODE = False
        self.x = sx
        self.y = sy
        self.width = width
        self.height = height
        self.bg_color = bg_color
        self.fg_color = fg_color
        self.max_val = max_val
        self.min_val = min_val
        self.cur_val = start_val
        self.incr = (max_val - min_val) / 127
        val_norm = (float(min_val + self.cur_val)) / (max_val - min_val)
        self.old_mouseY = -1000

        pygame.draw.arc(screen,self.bg_color, (self.x,self.y,self.width,self.height), -0.25*math.pi, -0.75*math.pi, 10)
        pygame.draw.arc(screen,self.fg_color, (self.x,self.y,self.width,self.height),-0.25*math.pi + (1.5 * math.pi * (val_norm)) , 1.25*math.pi, 10)
       
        pygame.display.update(pygame.Rect(self.x,self.y,self.width,self.height))

    def draw(self):
                
        if click[0] == 0 and self.DRAG_MODE == True:
            self.DRAG_MODE = False

        # if mouse[0] > sx and mouse[0] < sx+width and mouse[1] > sy and mouse[1] < sy+height:
        if click[0] == 1 and mouse[0] > self.x and mouse[0] < self.x+self.width and mouse[1] > self.y and mouse[1] < self.y+self.height:
            self.DRAG_MODE = True
        
        if self.DRAG_MODE and click[0] == 1:
            mouseY = mouse[1]
            # print(mouseY, self.old_mouseY)
            if mouseY < self.old_mouseY:
                self.cur_val = np.clip(self.cur_val - self.incr, self.min_val, self.max_val)
            elif mouseY > self.old_mouseY:
                self.cur_val = np.clip(self.cur_val + self.incr, self.min_val, self.max_val)
            else:
                return


            val_norm = (float(self.min_val + self.cur_val)) / (self.max_val - self.min_val)

            pygame.draw.arc(screen,self.bg_color, (self.x,self.y,self.width,self.height), -0.25*math.pi, -0.75*math.pi, 10)
           
            pygame.draw.arc(screen,self.fg_color, (self.x,self.y,self.width,self.height),-0.25*math.pi + (1.5 * math.pi * (val_norm)) , 1.25*math.pi, 10)

            pygame.display.update(pygame.Rect(self.x,self.y,self.width,self.height))
            
            if self.old_mouseY != mouseY:
                self.old_mouseY = mouseY

    

knob = Knob(100,50,100,100,(0,0,0),(255,0,0),0.0,1.0, 0.5)
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                pygame.quit()
                sys.exit()
        mouse = pygame.mouse.get_pos()
        click = pygame.mouse.get_pressed()
    
    knob.draw()
    # slider(100,120,"test2",1000,50,(255,255,255),(220,220,220),1,0,25,10,100)