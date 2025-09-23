import pygame
from rocket_race import RocketRace
from settings import WIDTH, HEIGHT

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
race = RocketRace(screen)
winner = race.run()
print(winner)
