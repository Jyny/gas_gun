import pygame, sys, os
from pygame.locals import *
os.environ["SDL_FBDEV"] = "/dev/fb0"

# set up the colors
BLACK = (  0,   0,   0)
WHITE = (255, 255, 255)
RED   = (255,   0,   0)
GREEN = (  0, 255,   0)
BLUE  = (  0,   0, 255)

pygame.init()

# set up the window
pygame.mouse.set_visible(False)
DISPLAYSURF = pygame.display.set_mode([640, 480])

# draw on the surface object
DISPLAYSURF.fill(WHITE)

# run the game loop
while True:
    pygame.display.update()
