import pygame, sys
from settings import WIDTH, HEIGHT, WHITE, RED, BLUE, DARK

def end_screen(screen, winner):
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 46, True)
    small = pygame.font.SysFont("Arial", 26)

    if winner == "URSS":
        title = "URSS venceu a Corrida Espacial!"
        lines = [
            "A União Soviética pousou primeiro e mudou o curso da história.",
            "A propaganda soviética dominou manchetes e a balança geopolítica se inclinou ao Leste.",
            "Uma nova era tecnológica sob forte influência socialista começou."
        ]
        color = RED
    else:
        title = "EUA venceu a Corrida Espacial!"
        lines = [
            "Os Estados Unidos chegaram primeiro à Lua, consolidando sua liderança.",
            "A cultura e a ciência ocidental se tornaram referência global.",
            "Uma nova etapa da Guerra Fria foi vencida pelo bloco capitalista."
        ]
        color = BLUE

    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()
        screen.fill(DARK)
        t = font.render(title, True, color)
        screen.blit(t, (WIDTH//2 - t.get_width()//2, 180))

        for i, line in enumerate(lines):
            s = small.render(line, True, WHITE)
            screen.blit(s, (WIDTH//2 - s.get_width()//2, 270 + i*40))

        press = small.render("Pressione ESC para sair", True, WHITE)
        screen.blit(press, (WIDTH//2 - press.get_width()//2, HEIGHT - 100))

        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]:
            pygame.quit(); sys.exit()

        pygame.display.flip()
        clock.tick(30)
