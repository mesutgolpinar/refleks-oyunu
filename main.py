# -*- coding: utf-8 -*-
import pygame
import random
import sys
import asyncio

# --- AYARLAR ---
WIDTH, HEIGHT = 800, 600
WHITE = (255, 255, 255)
BLUE = (50, 150, 255)
GREEN = (50, 255, 50)
RED = (255, 50, 50)
DARK_BG = (20, 20, 30)

class Particle:
    def __init__(self, pos, color):
        self.pos = pos
        self.color = color
        self.radius = 10
        self.alpha = 255
        self.dead = False

    def update(self):
        self.radius += 5
        self.alpha -= 15
        if self.alpha <= 0: self.dead = True

    def draw(self, surface):
        if self.alpha > 0:
            s = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*self.color, self.alpha), (self.radius, self.radius), self.radius, 3)
            surface.blit(s, (self.pos[0] - self.radius, self.pos[1] - self.radius))

class CircleGame:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Refleks Master")
        
        try:
            self.sound_glup = pygame.mixer.Sound("glup.ogg")
            self.sound_boom = pygame.mixer.Sound("explosion.ogg")
        except:
            self.sound_glup = self.sound_boom = None

        self.font = pygame.font.SysFont("Arial", 24, bold=True)
        self.big_font = pygame.font.SysFont("Arial", 40, bold=True)
        self.clock = pygame.time.Clock()
        
        self.state = "START" # START, PLAYING, GAMEOVER
        self.reset_game()

    def reset_game(self):
        self.score = 0
        self.lives = 3
        self.level = 1
        self.time_left = 30.0 # 30 saniye ile baslar
        self.blue_count = 0   # Kombo takibi icin
        self.circles = []
        self.particles = []
        self.spawn_timer = 0

    def spawn_circle(self):
        x = random.randint(50, WIDTH - 50)
        y = random.randint(50, HEIGHT - 50)
        color = GREEN if random.random() < 0.25 else BLUE
        self.circles.append({'pos': (x, y), 'color': color, 'time': pygame.time.get_ticks()})

    def update_logic(self, dt):
        if self.state != "PLAYING": return

        self.time_left -= dt # Sureden dus
        if self.time_left <= 0 or self.lives <= 0:
            self.time_left = 0
            self.state = "GAMEOVER"

        current_time = pygame.time.get_ticks()
        self.level = (self.score // 150) + 1
        duration = max(400, 1500 - (self.level * 100))
        
        if current_time - self.spawn_timer > max(300, 800 - (self.level * 50)):
            self.spawn_circle()
            self.spawn_timer = current_time

        self.circles = [c for c in self.circles if current_time - c['time'] < duration]
        for p in self.particles[:]:
            p.update()
            if p.dead: self.particles.remove(p)

    def draw(self):
        self.screen.fill(DARK_BG)
        
        if self.state == "START":
            self.draw_text("REFELEKS TESTI", self.big_font, WHITE, HEIGHT//2 - 100)
            self.draw_text("Mavileri vur +10 Puan", self.font, BLUE, HEIGHT//2 - 20)
            self.draw_text("Yesillerden kac -1 Can", self.font, GREEN, HEIGHT//2 + 20)
            self.draw_text("Her 5 mavide +5 Saniye!", self.font, WHITE, HEIGHT//2 + 60)
            self.draw_text("BASLAMAK ICIN TIKLA", self.font, RED, HEIGHT//2 + 120)
        
        elif self.state == "PLAYING":
            # UI
            s_txt = self.font.render(f"PUAN: {self.score}", True, WHITE)
            t_txt = self.font.render(f"SURE: {int(self.time_left)}s", True, WHITE if self.time_left > 10 else RED)
            l_txt = self.font.render(f"CAN: {self.lives}", True, RED)
            self.screen.blit(s_txt, (20, 20))
            self.screen.blit(t_txt, (WIDTH//2 - 40, 20))
            self.screen.blit(l_txt, (WIDTH - 120, 20))

            for c in self.circles:
                pygame.draw.circle(self.screen, c['color'], c['pos'], 25)
                pygame.draw.circle(self.screen, WHITE, c['pos'], 25, 2)
            for p in self.particles: p.draw(self.screen)

        elif self.state == "GAMEOVER":
            self.draw_text("OYUN BITTI", self.big_font, RED, HEIGHT//2 - 50)
            self.draw_text(f"TOPLAM PUAN: {self.score}", self.font, WHITE, HEIGHT//2 + 10)
            self.draw_text("Yeniden baslamak icin 'R' tusuna bas", self.font, WHITE, HEIGHT//2 + 60)

        pygame.display.flip()

    def draw_text(self, text, font, color, y_pos):
        surf = font.render(text, True, color)
        rect = surf.get_rect(center=(WIDTH//2, y_pos))
        self.screen.blit(surf, rect)

async def main():
    game = CircleGame()
    last_time = pygame.time.get_ticks()

    while True:
        current_time = pygame.time.get_ticks()
        dt = (current_time - last_time) / 1000.0
        last_time = current_time

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                if game.state == "START":
                    game.state = "PLAYING"
                elif game.state == "PLAYING":
                    m_pos = event.pos
                    for c in game.circles[:]:
                        dx, dy = c['pos'][0]-m_pos[0], c['pos'][1]-m_pos[1]
                        if (dx**2 + dy**2)**0.5 < 25:
                            game.particles.append(Particle(c['pos'], c['color']))
                            if c['color'] == BLUE:
                                game.score += 10
                                game.blue_count += 1
                                if game.sound_glup: game.sound_glup.play()
                                # 5 Mavide 5 Saniye Bonusu
                                if game.blue_count % 5 == 0:
                                    game.time_left += 5
                            else:
                                game.lives -= 1
                                if game.sound_boom: game.sound_boom.play()
                            game.circles.remove(c)
                            break
            
            if event.type == pygame.KEYDOWN and game.state == "GAMEOVER" and event.key == pygame.K_r:
                game.reset_game()
                game.state = "PLAYING"

        game.update_logic(dt)
        game.draw()
        await asyncio.sleep(0)
        game.clock.tick(60)

if __name__ == "__main__":
    asyncio.run(main())
