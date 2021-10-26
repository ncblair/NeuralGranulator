
# https://stackoverflow.com/questions/28032822/how-to-insert-a-slider-in-pygame
import pygame
import sys
import math
import numpy as np

from pygame.locals import *

from config import WINDOW_SIZE


class Knob :
   
    def __init__(self,screen,sx,sy,width,height,bg_color,fg_color,min_val, max_val,start_val):
        self.INCREMENT_RES = 64
        self.drag_mode = False
        self.screen = screen
        self.screen_size = self.screen.get_width()
        self.x = sx * self.screen_size / WINDOW_SIZE
        self.y = sy * self.screen_size / WINDOW_SIZE
        self.width = width * self.screen_size / WINDOW_SIZE
        self.height = height * self.screen_size / WINDOW_SIZE
        self.bg_color = bg_color
        self.fg_color = fg_color
        self.max_val = max_val
        self.min_val = min_val
        self.cur_val = start_val
        self.old_val = start_val
        self.incr = (max_val - min_val) / self.INCREMENT_RES
        val_norm = (float(min_val + self.cur_val)) / (max_val - min_val)
        self.old_mouseY = 0

        pygame.draw.arc(self.screen,self.bg_color, (self.x,self.y,self.width,self.height), -0.25*math.pi, -0.75*math.pi, 10)
        pygame.draw.arc(self.screen,self.fg_color, (self.x,self.y,self.width,self.height),-0.25*math.pi + (1.5 * math.pi * (val_norm)) , 1.25*math.pi, 10)
       
        # pygame.display.update(pygame.Rect(self.x,self.y,self.width,self.height))


    def draw(self, mouse, click, toggle_on):
        mouseY = mouse[1]

        if click[0] == 0 and self.drag_mode == True:
            self.drag_mode = False

        # if mouse[0] > sx and mouse[0] < sx+width and mouse[1] > sy and mouse[1] < sy+height:
        if toggle_on and click[0] == 1 and mouse[0] > self.x and mouse[0] < self.x+self.width and mouse[1] > self.y and mouse[1] < self.y+self.height:
            self.drag_mode = True
        
        self.old_val = self.cur_val
        if self.drag_mode and click[0] == 1:
            mouseY_diff = mouseY - self.old_mouseY
            # print(mouseY, self.old_mouseY)
            if mouseY_diff < 0:
                self.cur_val = np.clip(self.cur_val + self.incr, self.min_val, self.max_val)
            elif mouseY_diff > 0:
                self.cur_val = np.clip(self.cur_val - self.incr, self.min_val, self.max_val)


        val_norm = (float(self.min_val + self.cur_val)) / (self.max_val - self.min_val)

        pygame.draw.arc(self.screen,self.bg_color, (self.x,self.y,self.width,self.height), -0.25*math.pi, -0.75*math.pi, 10)
       
        pygame.draw.arc(self.screen,self.fg_color, (self.x,self.y,self.width,self.height),-0.25*math.pi + (1.5 * math.pi * (1-val_norm)) , 1.25*math.pi, 10)

        # pygame.display.update(pygame.Rect(self.x,self.y,self.width,self.height))
            
        self.old_mouseY = mouseY
    
        return self.drag_mode

    

if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    screenColor = (255,255,255)
    screen.fill(screenColor)
    pygame.display.update(pygame.Rect(0,0,800,600))
    knob = Knob(screen,100,50,100,100,(0,0,0),(255,0,0),0.0,1.0, 0.5)
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    pygame.quit()
                    sys.exit()
        
        knob.draw(pygame.mouse.get_pos(), pygame.mouse.get_pressed())