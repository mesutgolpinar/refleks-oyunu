# -*- coding: utf-8 -*-
import pygame
import random
import sys
import asyncio
import math

# --- AYARLAR ---
WIDTH, HEIGHT = 800, 600
WHITE = (255, 255, 255)
BLUE = (50, 150, 255)
GREEN = (50, 255, 50)
RED = (255, 50, 50)
GOLD = (255, 215, 0)
DARK_BG = (15, 15, 25)

class Particle:
    def __init__(self, pos, color):
        self.pos = list(pos)
        self.color = color
        self.vel = [random.uniform(-4, 4), random.uniform(-4, 4)]
        self.life = 255
        self.size = random.randint(3, 6)

    def update(self):
        self.pos[0] += self.vel[0]
        self.pos[1] += self.vel[1]
        self.life -= 12
        if self.life < 0: self.life = 0

    def draw(self, surface):
        s = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        pygame.draw.rect(s, (*self.color, self.life), (0, 0, self.size, self.size))
        surface.blit(s, (self.pos[0], self.pos[1]))

class CircleGame:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Refleks Master Pro")
        
        try:
            self.sound_glup = pygame.mixer.Sound("glup.ogg")
            self.sound_boom = pygame.mixer.Sound("explosion.ogg")
        except:
            self.sound_glup = self.sound_boom = None

        self.font = pygame.font.SysFont("Arial", 22, bold=True)
        self.big_font = pygame.font.SysFont("Arial", 50, bold=True)
        self.clock = pygame.time.Clock()
        self.state = "START"
        self.reset_game()

    def reset_game(self):
        self.score = 0
        self.lives = 3
        self.time_left = 30.0  # Sure 30'dan basliyor
        self.combo = 0
        self.blue_hit_count = 0 
        self.circles = []
        self.particles = []
        self.spawn_timer = 0
        self.freeze_timer = 0 # Zaman durdurma mekanigini yonetir

    def spawn_circle(self):
        x = random.randint(60, WIDTH - 60)
        y = random.randint(80, HEIGHT - 60)
        rand = random.random()
        
        if rand < 0.05: # %5 Altin
            color, c_type = GOLD, "GOLD"
        elif rand < 0.25: # %20 Yesil
            color, c_type = GREEN, "BAD"
        else: # %75 Mavi
            color, c_type = BLUE, "GOOD"
            
        self.circles.append({'pos': (x, y), 'color': color, 'type': c_type, 'time': pygame.time.get_ticks()})

    def update_logic(self, dt):
        if self.state != "PLAYING": return

        # Zaman Durdurma Kontrolu
        if self.freeze_timer > 0:
            self.freeze_timer -= dt
        else:
            self.time_left -= dt

        if self.time_left <= 0 or self.lives <= 0:
            self.state = "GAMEOVER"

        current_time = pygame.time.get_ticks()
        self.level = (self.score // 200) + 1
        
        spawn_rate = max(250, 900 - (self.level * 60))
        if current_time - self.spawn_timer > spawn_rate:
            self.spawn_circle()
            self.spawn_timer = current_time

        duration = max(400, 1600 - (self.level * 120))
        self.circles = [c for c in self.circles if current_time - c['time'] < duration]

        for p in self.particles[:]:
            p.update()
            if p.life <= 0: self.particles.remove(p)

    def draw(self):
        self.screen.fill(DARK_BG)
        
        if self.state == "START":
            self.draw_center_text([
                ("REFLEKS MASTER PRO", self.big_font, GOLD, -100),
                ("Maviler: +10 Puan & Kombo", self.font, BLUE, -30),
                ("Altin: Zamani Durdurur & Temizlik", self.font, GOLD, 10),
                ("Her 5 Mavi: +3 Saniye Bonus!", self.font, WHITE, 50),
                ("BASLAMAK ICIN TIKLA", self.font, RED, 120)
            ])
        elif self.state == "PLAYING":
            # HUD
            s_txt = self.font.render(f"SKOR: {self.score}", True, WHITE)
            t_color = GOLD if self.freeze_timer > 0 else (RED if self.time_left < 5 else WHITE)
            t_txt = self.font.render(f"SURE: {max(0, int(self.time_left))}s {'(DONDU)' if self.freeze_timer > 0 else ''}", True, t_color)
            c_txt = self.font.render(f"COMBO: {self.combo}", True, GOLD if self.combo >= 5 else WHITE)
            
            self.screen.blit(s_txt, (20, 20))
            self.screen.blit(t_txt, (WIDTH//2 - 60, 20))
            self.screen.blit(c_txt, (WIDTH - 150, 20))

            for c in self.circles:
                pygame.draw.circle(self.screen, c['color'], c['pos'], 30)
                pygame.draw.circle(self.screen, WHITE, c['pos'], 30, 2)
            for p in self.particles: p.draw(self.screen)

        elif self.state == "GAMEOVER":
            self.draw_center_text([
                ("OYUN BITTI", self.big_font, RED, -50),
                (f"SKORUN: {self.score}", self.font, WHITE, 10),
                ("Yeniden Baslatmak Icin 'R'ye Bas", self.font, WHITE, 70)
            ])

        pygame.display.flip()

    def draw_center_text(self, items):
        for text, font, color, y in items:
            surf = font.render(text, True, color)
            rect = surf.get_rect(center=(WIDTH//2, HEIGHT//2 + y))
            self.screen.blit(surf, rect)

async def main():
    game = CircleGame()
    last_time = pygame.time.get_ticks()

    while True:
        dt = (pygame.time.get_ticks() - last_time) / 1000.0
        last_time = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                if game.state == "START":
                    game.state = "PLAYING"
                elif game.state == "PLAYING":
                    m_pos = event.pos
                    hit_target = False
                    for c in game.circles[:]:
                        if math.hypot(c['pos'][0]-m_pos[0], c['pos'][1]-m_pos[1]) < 35:
                            # Patlama Efekti
                            for _ in range(10): game.particles.append(Particle(c['pos'], c['color']))
                            
                            if c['type'] == "GOOD":
                                game.score += 10
                                game.combo += 1
                                game.blue_hit_count += 1
                                if game.sound_glup: game.sound_glup.play()
                                # 5 Vurusta 3 Saniye Kurali
                                if game.blue_hit_count % 5 == 0:
                                    game.time_left += 3
                            elif c['type'] == "GOLD":
                                game.freeze_timer = 5.0 # Zaman 5 saniye donar
                                game.circles = [obj for obj in game.circles if obj['type'] != "BAD"]
                                if game.sound_glup: game.sound_glup.play()
                            else: # YESIL
                                game.lives -= 1
                                game.combo = 0
                                if game.sound_boom: game.sound_boom.play()
                            
                            game.circles.remove(c)
                            hit_target = True
                            break
                    if not hit_target: game.combo = 0

            if event.type == pygame.KEYDOWN and game.state == "GAMEOVER" and event.key == pygame.K_r:
                game.reset_game()
                game.state = "PLAYING"

        game.update_logic(dt)
        game.draw()
        await asyncio.sleep(0)
        game.clock.tick(60)

if __name__ == "__main__":
    asyncio.run(main())
