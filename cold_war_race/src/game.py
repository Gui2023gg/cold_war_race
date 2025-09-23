import pygame
from settings import WIDTH, HEIGHT, WHITE, RED, BLUE, LIGHT_RED, LIGHT_BLUE
from player import Player

class Game:
    def __init__(self, screen):
        self.screen = screen

        # Criar jogadores
        self.player1 = Player(100, HEIGHT//2, LIGHT_RED, {
            "up": pygame.K_w,
            "down": pygame.K_s,
            "left": pygame.K_a,
            "right": pygame.K_d
        })

        self.player2 = Player(WIDTH-140, HEIGHT//2, LIGHT_BLUE, {
            "up": pygame.K_UP,
            "down": pygame.K_DOWN,
            "left": pygame.K_LEFT,
            "right": pygame.K_RIGHT
        })

    def update(self):
      keys = pygame.key.get_pressed()
      self.player1.handle_input(keys, "left")
      self.player2.handle_input(keys, "right")


    def draw(self):
        # Fundo branco
        self.screen.fill(WHITE)

        # Metade esquerda (URSS - vermelho)
        pygame.draw.rect(self.screen, RED, (0, 0, WIDTH//2, HEIGHT))

        # Metade direita (EUA - azul)
        pygame.draw.rect(self.screen, BLUE, (WIDTH//2, 0, WIDTH//2, HEIGHT))

        # Linha divisória
        pygame.draw.line(self.screen, WHITE, (WIDTH//2, 0), (WIDTH//2, HEIGHT), 5)

        # Desenhar jogadores
        self.player1.draw(self.screen)
        self.player2.draw(self.screen)
