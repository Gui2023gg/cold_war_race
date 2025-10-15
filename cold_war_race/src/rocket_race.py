import pygame, random, os
from settings import WIDTH, HEIGHT, WHITE, RED, BLUE, FPS

class RocketRace:
    def __init__(self, screen, advantage1=0, advantage2=0):
        self.screen = screen
        self.clock = pygame.time.Clock()

        assets_dir = os.path.join(os.path.dirname(__file__), "..", "assets", "sprites")
        assets_dir = os.path.normpath(assets_dir)

        def load_image(name, size, fallback_color):
            path = os.path.join(assets_dir, name)
            try:
                img = pygame.image.load(path).convert_alpha()
                img = pygame.transform.scale(img, size)
                return img
            except Exception:
                surf = pygame.Surface(size, pygame.SRCALPHA)
                surf.fill(fallback_color)
                return surf

        # Fundo procedural estilo pixel art espacial
        self.bg_img = self.generate_space_background()

        # Estrelas piscando
        self.stars = []
        for _ in range(120):
            x = random.randint(0, WIDTH)
            y = random.randint(0, HEIGHT)
            radius = random.randint(1, 2)
            brightness = random.randint(150, 255)
            self.stars.append([x, y, radius, brightness])

        # Sprites foguetes
        self.rocket_img1 = load_image("rocket_red.png", (50, 80), (180, 40, 40))
        self.rocket_img2 = load_image("rocket_blue.png", (50, 80), (40, 80, 180))

        # Asteroides (3 variantes)
        self.asteroid_imgs = [
            load_image("asteroid4.png", (70, 70), (120, 100, 80)),
            load_image("asteroid5.png", (70, 70), (100, 90, 100)),
            load_image("asteroid6.png", (60, 60), (140, 120, 100)),
        ]
        self.asteroids = []

        # Power-up icons (place your icons in assets/sprites with these names)
        self.icon_map = {
            "shield": load_image("p_shield.png", (36,36), (200,200,200)),
            "double": load_image("p_double.png", (36,36), (200,200,200)),
            "blast":  load_image("p_blast.png", (36,36), (200,200,200)),
            "slow":   load_image("p_slow.png", (36,36), (200,200,200)),
        }

        # powerups currently on screen: list of dicts {rect,type,img,vy}
        self.powerups = []

        # Foguetes
        self.rocket1 = pygame.Rect(WIDTH//4 - 25, HEIGHT - 100, 50, 80)
        self.rocket2 = pygame.Rect(3*WIDTH//4 - 25, HEIGHT - 100, 50, 80)

        # Progresso inicial
        self.progress1 = advantage1
        self.progress2 = advantage2
        self.finish_line = 4000

        # Power-up state per player
        self.shield_end = [0, 0]     # ms timestamps
        self.multiplier = [1.0, 1.0] # progress multiplier (double power uses 2.0)
        self.slow_end = [0, 0]       # slowdown applied (when slow affects a player)

        # spawn timing
        self._last_power_spawn = pygame.time.get_ticks()
        self._next_power_interval = random.randint(5000, 10000)  # ms

    # === NOVO: Gerador de fundo procedural (mantive) ===
    def generate_space_background(self):
        bg = pygame.Surface((WIDTH, HEIGHT))
        bg.fill((5, 5, 20))  # fundo azul-escuro

        # --- Estrelas fixas ---
        for _ in range(250):
            x = random.randint(0, WIDTH-1)
            y = random.randint(0, HEIGHT-1)
            color_choice = random.choices(
                [(255, 255, 255), (200, 200, 255), (255, 200, 200), (200, 255, 200)],
                weights=[70, 15, 10, 5]
            )[0]
            bg.set_at((x, y), color_choice)

        # --- Nebulosas ---
        for _ in range(6):
            cx = random.randint(0, WIDTH)
            cy = random.randint(0, HEIGHT)
            max_radius = random.randint(100, 200)
            color = random.choice([(120, 20, 60), (80, 0, 100), (150, 40, 120)])

            for i in range(max_radius * 30):  # densidade
                angle = random.uniform(0, 6.28)
                dist = random.randint(0, max_radius)
                x = int(cx + dist * pygame.math.Vector2(1, 0).rotate_rad(angle).x)
                y = int(cy + dist * pygame.math.Vector2(1, 0).rotate_rad(angle).y)

                if 0 <= x < WIDTH and 0 <= y < HEIGHT:
                    old_color = bg.get_at((x, y))
                    new_color = (
                        (old_color[0] + color[0]) // 2,
                        (old_color[1] + color[1]) // 2,
                        (old_color[2] + color[2]) // 2
                    )
                    bg.set_at((x, y), new_color)

        return bg

    def spawn_asteroid(self):
        side = random.choice(["left", "right"])
        if side == "left":
            x = random.randint(0, WIDTH//2 - 60)
        else:
            x = random.randint(WIDTH//2, WIDTH - 60)
        y = random.randint(-300, -60)

        rect = pygame.Rect(x, y, 60, 60)

        # Escolhe a variante com pesos para variar mais
        img = random.choices(
            self.asteroid_imgs,
            weights=[3, 2, 1],  # asteroid4 mais comum, asteroid6 mais raro
            k=1
        )[0]

        self.asteroids.append([rect, img])

    # === Power-ups ===
    def try_spawn_powerup(self):
        now = pygame.time.get_ticks()
        if now - self._last_power_spawn < self._next_power_interval:
            return
        self._last_power_spawn = now
        self._next_power_interval = random.randint(5000, 12000)

        ptype = random.choice(["shield", "double", "blast", "slow"])
        x = random.randint(40, WIDTH - 80)
        rect = pygame.Rect(x, -40, 36, 36)
        img = self.icon_map.get(ptype)
        vy = random.uniform(1.2, 2.2)
        self.powerups.append({"rect": rect, "type": ptype, "img": img, "vy": vy})

    def apply_powerup(self, owner_idx, ptype):
        now = pygame.time.get_ticks()
        if ptype == "shield":
            self.shield_end[owner_idx] = now + 10000  # 10s
        elif ptype == "double":
            self.multiplier[owner_idx] = 2.0
            # schedule multiplier reset after 5s
            pygame.time.set_timer(pygame.USEREVENT + 1 + owner_idx, 1, loops=1)  # dummy to ensure pygame has event loop
            # store end time
            if owner_idx == 0:
                self._double_end0 = now + 6000
            else:
                self._double_end1 = now + 6000
        elif ptype == "blast":
            # reduz o progresso do oponente em 20% do seu progresso atual
            opp = 1 - owner_idx
            reduction = int(self.progress1 * 0.2) if opp == 0 else int(self.progress2 * 0.2)
            if opp == 0:
                self.progress1 = max(0, self.progress1 - reduction)
            else:
                self.progress2 = max(0, self.progress2 - reduction)
        elif ptype == "slow":
            opp = 1 - owner_idx
            # aplica slow ao oponente por 5s (multiplicador 0.5)
            self.slow_end[opp] = now + 5000

    def powerup_timers_update(self):
        now = pygame.time.get_ticks()
        # reset double multipliers if expired (we used attributes set above)
        if hasattr(self, "_double_end0") and self._double_end0 <= now:
            self.multiplier[0] = 1.0
            del self._double_end0
        if hasattr(self, "_double_end1") and self._double_end1 <= now:
            self.multiplier[1] = 1.0
            del self._double_end1
        # reset shield (we just check end times when needed)
        # apply slow effect: slow reduces multiplier for the affected player
        for i in (0,1):
            if self.slow_end[i] > now:
                # make sure slow overrides multiplier effect multiplicatively
                # if double active, effective multiplier will be multiplier*0.5 in run()
                pass
            else:
                # expired
                self.slow_end[i] = 0

    def victory_screen(self, winner):
        font = pygame.font.SysFont("arial", 50, True)
        small_font = pygame.font.SysFont("arial", 30)

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    raise SystemExit
                if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                    return

            self.screen.fill((0,0,0))

            if winner == "URSS":
                text = font.render("URSS venceu a corrida espacial!", True, RED)
                story = [
                    
                ]
            else:
                text = font.render("EUA venceu a corrida espacial!", True, BLUE)
                story = [
                    
                ]

            self.screen.blit(text, (WIDTH//2 - text.get_width()//2, 200))

            for i, line in enumerate(story):
                msg = small_font.render(line, True, WHITE)
                self.screen.blit(msg, (WIDTH//2 - msg.get_width()//2, 300 + i*40))

            hint = small_font.render("Pressione qualquer tecla ou clique para continuar", True, (200,200,200))
            self.screen.blit(hint, (WIDTH//2 - hint.get_width()//2, HEIGHT - 80))

            pygame.display.flip()
            self.clock.tick(30)

    def get_asteroid_hitbox(self, asteroid_rect):
        shrink = 0.5
        new_w = int(asteroid_rect.width * shrink)
        new_h = int(asteroid_rect.height * shrink)
        new_x = asteroid_rect.x + (asteroid_rect.width - new_w)//2
        new_y = asteroid_rect.y + (asteroid_rect.height - new_h)//2
        return pygame.Rect(new_x, new_y, new_w, new_h)

    def run(self):
        running = True
        frame_count = 0

        # fonts for power-up timers
        timer_font = pygame.font.SysFont("arial", 16)

        while running:
            explosions = []
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    raise SystemExit

            # spawn powerups occasionally
            self.try_spawn_powerup()

            keys = pygame.key.get_pressed()

            # Controles rocket1 (WASD)
            if keys[pygame.K_w]: self.rocket1.y -= 3
            if keys[pygame.K_s]: self.rocket1.y += 4
            if keys[pygame.K_a]: self.rocket1.x -= 4
            if keys[pygame.K_d]: self.rocket1.x += 3

            # Controles rocket2 (Setas)
            if keys[pygame.K_UP]: self.rocket2.y -= 3
            if keys[pygame.K_DOWN]: self.rocket2.y += 4
            if keys[pygame.K_LEFT]: self.rocket2.x -= 4
            if keys[pygame.K_RIGHT]: self.rocket2.x += 3

            # Progresso automático usando multipliers and slow
            now = pygame.time.get_ticks()
            # determine effective multipliers (slow halves progress)
            eff_mult1 = self.multiplier[0] * (0.5 if self.slow_end[0] > now else 1.0)
            eff_mult2 = self.multiplier[1] * (0.5 if self.slow_end[1] > now else 1.0)

            self.progress1 += 1 * eff_mult1
            self.progress2 += 1 * eff_mult2

            # Limites de tela
            self.rocket1.clamp_ip(pygame.Rect(0, 0, WIDTH//2, HEIGHT))
            self.rocket2.clamp_ip(pygame.Rect(WIDTH//2, 0, WIDTH//2, HEIGHT))

            # Spawn asteroides
            frame_count += 1
            if frame_count % 27 == 0:
                for _ in range(3):
                    self.spawn_asteroid()

            # Move asteroides
            for ast in self.asteroids:
                rect, img = ast
                rect.y += 3
            self.asteroids = [a for a in self.asteroids if a[0].y < HEIGHT]

            # Powerups fall
            for pu in list(self.powerups):
                pu["rect"].y += int(pu["vy"])
                # remove if off-screen
                if pu["rect"].top > HEIGHT:
                    self.powerups.remove(pu)
                    continue
                # collision with rockets
                if pu["rect"].colliderect(self.rocket1):
                    self.apply_powerup(0, pu["type"])
                    if pu in self.powerups: self.powerups.remove(pu)
                    continue
                if pu["rect"].colliderect(self.rocket2):
                    self.apply_powerup(1, pu["type"])
                    if pu in self.powerups: self.powerups.remove(pu)
                    continue

            # Colisão foguete x asteroide
            asteroids_to_remove = []
            for ast in self.asteroids:
                rect, img = ast
                hitbox = self.get_asteroid_hitbox(rect)
                if self.rocket1.colliderect(hitbox):
                    # if shield active ignore damage
                    if self.shield_end[0] > now:
                        pass
                    else:
                        self.progress1 -= 60
                    asteroids_to_remove.append(ast)
                    explosions.append((rect.centerx, rect.centery))
                elif self.rocket2.colliderect(hitbox):
                    if self.shield_end[1] > now:
                        pass
                    else:
                        self.progress2 -= 60
                    asteroids_to_remove.append(ast)
                    explosions.append((rect.centerx, rect.centery))
            for ast in asteroids_to_remove:
                if ast in self.asteroids:
                    self.asteroids.remove(ast)

            # Impede progresso negativo
            self.progress1 = max(self.progress1, 0)
            self.progress2 = max(self.progress2, 0)

            # Chegada
            if self.progress1 >= self.finish_line:
                self.victory_screen("URSS")
                return "URSS"
            if self.progress2 >= self.finish_line:
                self.victory_screen("EUA")
                return "EUA"

            # update timers for powerups
            self.powerup_timers_update()

            # === Desenho ===
            self.screen.blit(self.bg_img, (0, 0))

            # Estrelas piscando (sobre o fundo)
            for star in self.stars:
                x, y, r, bright = star
                color = (bright, bright, bright)
                pygame.draw.circle(self.screen, color, (x, y), r)
                star[3] += random.choice([-10, -5, 0, 5, 10])
                star[3] = max(100, min(255, star[3]))

            # Linha divisória
            pygame.draw.line(self.screen, WHITE, (WIDTH//2, 0), (WIDTH//2, HEIGHT), 3)

            # Barra de progresso
            pygame.draw.line(self.screen, WHITE, (50, 30), (WIDTH-50, 30), 4)
            max_width = WIDTH - 100
            pygame.draw.rect(self.screen, RED, (50, 20, (self.progress1/self.finish_line)*max_width, 10))
            pygame.draw.rect(self.screen, BLUE, (50, 35, (self.progress2/self.finish_line)*max_width, 10))

            # Foguetes
            self.screen.blit(self.rocket_img1, self.rocket1)
            self.screen.blit(self.rocket_img2, self.rocket2)

            # Powerups: desenha ícones caindo
            for pu in self.powerups:
                if pu["img"]:
                    self.screen.blit(pu["img"], pu["rect"])
                else:
                    pygame.draw.rect(self.screen, (255,255,0), pu["rect"])

            # Asteroides
            for rect, img in self.asteroids:
                self.screen.blit(img, rect)

            # Explosões
            for pos in explosions:
                pygame.draw.circle(self.screen, (255, 80, 0), pos, 40)

            # Draw active power-up icons + timers near each rocket
            now = pygame.time.get_ticks()
            # player1 UI (left)
            ui_x1 = 20
            ui_y1 = 60
            if self.shield_end[0] > now:
                self.screen.blit(self.icon_map["shield"], (ui_x1, ui_y1))
                t = int((self.shield_end[0] - now) / 1000)
                txt = timer_font.render(str(t)+"s", True, (255,255,255))
                self.screen.blit(txt, (ui_x1+40, ui_y1+6))
            if hasattr(self, "_double_end0") and self._double_end0 > now:
                self.screen.blit(self.icon_map["double"], (ui_x1, ui_y1+36))
                t = int((self._double_end0 - now) / 1000)
                txt = timer_font.render(str(t)+"s", True, (255,255,255))
                self.screen.blit(txt, (ui_x1+40, ui_y1+36+6))
            if self.slow_end[0] > now:
                self.screen.blit(self.icon_map["slow"], (ui_x1, ui_y1+72))
                t = int((self.slow_end[0] - now) / 1000)
                txt = timer_font.render(str(t)+"s", True, (255,255,255))
                self.screen.blit(txt, (ui_x1+40, ui_y1+72+6))

            # player2 UI (right)
            ui_x2 = WIDTH - 120
            ui_y2 = 60
            if self.shield_end[1] > now:
                self.screen.blit(self.icon_map["shield"], (ui_x2, ui_y2))
                t = int((self.shield_end[1] - now) / 1000)
                txt = timer_font.render(str(t)+"s", True, (255,255,255))
                self.screen.blit(txt, (ui_x2+40, ui_y2+6))
            if hasattr(self, "_double_end1") and self._double_end1 > now:
                self.screen.blit(self.icon_map["double"], (ui_x2, ui_y2+36))
                t = int((self._double_end1 - now) / 1000)
                txt = timer_font.render(str(t)+"s", True, (255,255,255))
                self.screen.blit(txt, (ui_x2+40, ui_y2+36+6))
            if self.slow_end[1] > now:
                self.screen.blit(self.icon_map["slow"], (ui_x2, ui_y2+72))
                t = int((self.slow_end[1] - now) / 1000)
                txt = timer_font.render(str(t)+"s", True, (255,255,255))
                self.screen.blit(txt, (ui_x2+40, ui_y2+72+6))

            pygame.display.flip()
            self.clock.tick(FPS)
