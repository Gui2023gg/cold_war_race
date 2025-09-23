import pygame

class Player:
    def __init__(self, x, y, color, controls):
        self.rect = pygame.Rect(x, y, 40, 40)
        self.color = color
        self.controls = controls
        self.speed = 5

    def handle_input(self, keys, side):
     if keys[self.controls["up"]]:
        self.rect.y -= self.speed
        if keys[self.controls["down"]]:
          self.rect.y += self.speed
     if keys[self.controls["left"]]:
        self.rect.x -= self.speed
     if keys[self.controls["right"]]:
        self.rect.x += self.speed

    # Limites da tela
     if self.rect.y < 0:
        self.rect.y = 0
     if self.rect.y > 600 - self.rect.height:
        self.rect.y = 600 - self.rect.height

    # Impedir de invadir o lado do inimigo
        if side == "left" and self.rect.right > 400:  # WIDTH//2
          self.rect.right = 400
     if side == "right" and self.rect.left < 400:
        self.rect.left = 400


    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)
