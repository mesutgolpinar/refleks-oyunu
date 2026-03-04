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
    """Vurus aninda etrafa sacilan parcalari yoneten sinif"""
    def __init__(self, pos, color):
        self.pos = list(pos)
        self.color = color
        self.vel = [random.uniform(-4, 4), random.uniform(-4, 4)]
        self.life = 255
        self.size = random.randint(3, 6)

    def update(self):
        self.pos[0] += self.vel[0]
        self.pos[1] += self.vel[1]
        self.life -= 10
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
        pygame.display.set_caption("Refleks Pro")
        
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
        self.time_left = 30.0
        self.combo = 0
        self.max_combo = 0
        self.circles = []
        self.particles = []
        self.spawn_timer = 0
        self.combo_text_timer = 0

    def spawn_circle(self):
        x = random.randint(60, WIDTH - 60)
        y = random.randint(80, HEIGHT - 60)
        rand = random.random()
        
        if rand < 0.05: # %5 Altin Daire
            color = GOLD
            c_type = "GOLD"
        elif rand < 0.25: # %20 Yesil Daire
            color = GREEN
            c_type = "BAD"
        else: # %75 Mavi Daire
            color = BLUE
            c_type = "GOOD"
            
        self.circles.append({
            'pos': (x, y), 
            'color': color, 
            'type': c_type,
            'time': pygame.time.get_ticks()
        })

    def create_explosion(self, pos, color):
        for _ in range(12):
            self.particles.append(Particle(pos, color))

    def update_logic(self, dt):
        if self.state != "PLAYING": return

        self.time_left -= dt
        if self.time_left <= 0 or self.lives <= 0:
            self.state = "GAMEOVER"

        current_time = pygame.time.get_ticks()
        self.level = (self.score // 200) + 1
        
        # Spawn hizi level ile artar
        spawn_rate = max(250, 900 - (self.level * 60))
        if current_time - self.spawn_timer > spawn_rate:
            self.spawn_circle()
            self.spawn_timer = current_time

        # Dairelerin ekranda kalma suresi
        duration = max(400, 1600 - (self.level * 120))
        self.circles = [c for c in self.circles if current_time - c['time'] < duration]

        # Parcaciklari guncelle
        for p in self.particles[:]:
            p.update()
            if p.life <= 0: self.particles.remove(p)

        if self.combo_text_timer > 0:
            self.combo_text_timer -= 1

    def draw(self):
        self.screen.fill(DARK_BG)
        
        if self.state == "START":
            self.draw_ui_center()
        elif self.state == "PLAYING":
            self.draw_game_elements()
        elif self.state == "GAMEOVER":
            self.draw_game_over()

        pygame.display.flip()

    def draw_game_elements(self):
        # Stats
        s_txt = self.font.render(f"SKOR: {self.score}", True, WHITE)
        t_txt = self.font.render(f"SURE: {int(self.time_left)}s", True, WHITE if self.time_left > 5 else RED)
        c_txt = self.font.render(f"COMBO: {self.combo}", True, BLUE if self.combo < 5 else GOLD)
        self.screen.blit(s_txt, (20, 20))
        self.screen.blit(t_txt, (WIDTH//2 - 40, 20))
        self.screen.blit(c_txt, (WIDTH - 150, 20))

        # Circles
        for c in self.circles:
            pygame.draw.circle(self.screen, c['color'], c['pos'], 28) # Mobil icin +3px hitbox
            pygame.draw.circle(self.screen, WHITE, c['pos'], 28, 2)

        # Particles
        for p in self.particles: p.draw(self.screen)

        # Combo Popup
        if self.combo_text_timer > 0:
            c_msg = self.big_font.render(f"{self.combo} COMBO!", True, GOLD)
            self.screen.blit(c_msg, (WIDTH//2 - 100, HEIGHT//2))

    def draw_ui_center(self):
        texts = [
            ("REFLEKS PRO", self.big_font, GOLD, -100),
            ("Maviler: Puan & Combo", self.font, BLUE, -30),
            ("Altin: +5s & Temizlik", self.font, GOLD, 10),
            ("Yesiller: -1 Can", self.font, GREEN, 50),
            ("BASLAMAK ICIN TIKLA", self.font, RED, 120)
        ]
        for t, f, c, y in texts:
            surf = f.render(t, True, c)
            rect = surf.get_rect(center=(WIDTH//2, HEIGHT//2 + y))
            self.screen.blit(surf, rect)

    def draw_game_over(self):
        self.draw_ui_center() # Arkaplan metinleri icin
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        go_txt = self.big_font.render("OYUN BITTI", True, RED)
        sc_txt = self.font.render(f"Skor: {self.score} | Max Combo: {self.max_combo}", True, WHITE)
        rs_txt = self.font.render("Yeniden Baslat: 'R'", True, WHITE)
        self.screen.blit(go_txt, (WIDTH//2 - 130, HEIGHT//2 - 60))
        self.screen.blit(sc_txt, (WIDTH//2 - 120, HEIGHT//2))
        self.screen.blit(rs_txt, (WIDTH//2 - 80, HEIGHT//2 + 60))

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
                    hit = False
                    for c in game.circles[:]:
                        dist = math.hypot(c['pos'][0]-m_pos[0], c['pos'][1]-m_pos[1])
                        if dist < 35: # Genisletilmis hitbox
                            game.create_explosion(c['pos'], c['color'])
                            if c['type'] == "GOOD":
                                game.combo += 1
                                game.max_combo = max(game.combo, game.max_combo)
                                multiplier = 1 + (game.combo // 5)
                                game.score += 10 * multiplier
                                if game.combo % 5 == 0: 
                                    game.combo_text_timer = 40
                                    game.time_left += 2
                                if game.sound_glup: game.sound_glup.play()
                            elif c['type'] == "GOLD":
                                game.time_left += 5
                                game.circles = [obj for obj in game.circles if obj['type'] != "BAD"]
                                if game.sound_glup: game.sound_glup.play()
                            else:
                                game.lives -= 1
                                game.combo = 0
                                if game.sound_boom: game.sound_boom.play()
                            game.circles.remove(c)
                            hit = True
                            break
                    if not hit: # Bosa tiklama kombo sifirlar
                        game.combo = 0

            if event.type == pygame.KEYDOWN and game.state == "GAMEOVER" and event.key == pygame.K_r:
                game.reset_game()
                game.state = "PLAYING"

        game.update_logic(dt)
        game.draw()
        await asyncio.sleep(0)
        game.clock.tick(60)

if __name__ == "__main__":
    asyncio.run(main())
