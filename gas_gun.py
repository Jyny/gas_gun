import pygame, sys, os
from pygame.locals import *

os.environ["SDL_FBDEV"] = "/dev/fb0"

BLACK = (  0,   0,   0)
WHITE = (255, 255, 255)
RED   = (255,   0,   0)
GREEN = (  0, 255,   0)
BLUE  = (  0,   0, 255)

pygame.init()
pygame.mouse.set_visible(False)

screen = pygame.display.set_mode([640, 480])
screen.fill(WHITE)

while True:
    pygame.display.update()
