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
DARK_RED = (150, 0, 0)
DARK_BG = (15, 15, 25)

class Particle:
    def __init__(self, pos, color):
        self.pos = list(pos)
        self.color = color
        self.vel = [random.uniform(-5, 5), random.uniform(-5, 5)]
        self.life = 255
        self.size = random.randint(4, 7)

    def update(self):
        self.pos[0] += self.vel[0]
        self.pos[1] += self.vel[1]
        self.life -= 15
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
            self.sound_gold = pygame.mixer.Sound("gold.ogg")
            pygame.mixer.music.load("main.ogg")
        except:
            self.sound_glup = self.sound_boom = self.sound_gold = None

        self.font = pygame.font.SysFont("Arial", 22, bold=True)
        self.big_font = pygame.font.SysFont("Arial", 55, bold=True)
        self.combo_font = pygame.font.SysFont("Verdana", 90, bold=True)
        self.clock = pygame.time.Clock()
        self.state = "START"
        self.reset_game()

    def reset_game(self):
        self.score = 0
        self.lives = 3
        self.time_left = 30.0
        self.combo = 0
        self.circles = []
        self.particles = []
        self.spawn_timer = 0
        self.combo_msg_timer = 0
        try: pygame.mixer.music.stop()
        except: pass

    def spawn_circle(self):
        x = random.randint(70, WIDTH - 70)
        y = random.randint(110, HEIGHT - 90)
        rand = random.random()
        
        if rand < 0.05: # %5 Altin
            color, c_type = GOLD, "GOLD"
        elif rand < 0.13: # %8 Kirmizi (Zaman Ceza)
            color, c_type = DARK_RED, "TIME_THIEF"
        elif rand < 0.30: # %17 Yesil (Combo Ceza)
            color, c_type = GREEN, "BAD"
        else: # %70 Mavi
            color, c_type = BLUE, "GOOD"
            
        self.circles.append({'pos': (x, y), 'color': color, 'type': c_type, 'time': pygame.time.get_ticks()})

    def update_logic(self, dt):
        if self.state != "PLAYING": return

        self.time_left -= dt
        if self.time_left <= 0 or self.lives <= 0:
            self.time_left = 0
            self.state = "GAMEOVER"
            try: pygame.mixer.music.fadeout(1000)
            except: pass

        if self.combo_msg_timer > 0: self.combo_msg_timer -= 1

        current_time = pygame.time.get_ticks()
        self.level = (self.score // 200) + 1
        spawn_rate = max(240, 850 - (self.level * 65))
        
        if current_time - self.spawn_timer > spawn_rate:
            self.spawn_circle()
            self.spawn_timer = current_time

        duration = max(400, 1700 - (self.level * 130))
        self.circles = [c for c in self.circles if current_time - c['time'] < duration]

        for p in self.particles[:]:
            p.update()
            if p.life <= 0: self.particles.remove(p)

    def draw(self):
        self.screen.fill(DARK_BG)
        
        if self.state == "START":
            self.draw_center_text([
                ("REFLEKS MASTER", self.big_font, GOLD, -120),
                ("Mavi: +10 Puan & Combo", self.font, BLUE, -40),
                ("Yesil: Comboyu Sifirlar!", self.font, GREEN, 0),
                ("Kirmizi: -3 Saniye Ceza!", self.font, RED, 40),
                ("Altin: +5 Saniye & Temizlik", self.font, GOLD, 80),
                ("DOKUN VE BASLAT", self.font, WHITE, 160)
            ])
        elif self.state == "PLAYING":
            s_txt = self.font.render(f"SKOR: {self.score}", True, WHITE)
            t_txt = self.font.render(f"SURE: {int(self.time_left)}s", True, RED if self.time_left < 6 else WHITE)
            c_txt = self.font.render(f"COMBO: {self.combo}", True, GOLD if self.combo >= 5 else WHITE)
            self.screen.blit(s_txt, (20, 20))
            self.screen.blit(t_txt, (WIDTH//2 - 40, 20))
            self.screen.blit(c_txt, (WIDTH - 150, 20))

            for c in self.circles:
                pygame.draw.circle(self.screen, c['color'], c['pos'], 32)
                pygame.draw.circle(self.screen, WHITE, c['pos'], 32, 2)
            
            for p in self.particles: p.draw(self.screen)

            if self.combo_msg_timer > 0:
                msg = self.combo_font.render("COMBO!", True, GOLD)
                rect = msg.get_rect(center=(WIDTH//2, HEIGHT//2))
                self.screen.blit(msg, rect)

        elif self.state == "GAMEOVER":
            self.draw_center_text([
                ("OYUN BITTI", self.big_font, RED, -60),
                (f"SKORUN: {self.score}", self.font, WHITE, 10),
                ("YENIDEN BASLATMAK ICIN DOKUN", self.font, GOLD, 80)
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
                if game.state == "START" or game.state == "GAMEOVER":
                    game.reset_game()
                    game.state = "PLAYING"
                    try: pygame.mixer.music.play(-1)
                    except: pass
                elif game.state == "PLAYING":
                    m_pos = event.pos
                    hit_target = False
                    for c in game.circles[:]:
                        if math.hypot(c['pos'][0]-m_pos[0], c['pos'][1]-m_pos[1]) < 40:
                            for _ in range(12): game.particles.append(Particle(c['pos'], c['color']))
                            
                            if c['type'] == "GOOD":
                                game.score += 10
                                game.combo += 1
                                if game.sound_glup: game.sound_glup.play()
                                if game.combo > 0 and game.combo % 5 == 0:
                                    game.time_left += 3
                                    game.combo_msg_timer = 45
                            elif c['type'] == "GOLD":
                                game.time_left += 5
                                game.circles = [obj for obj in game.circles if obj['type'] != "BAD"]
                                if game.sound_gold: game.sound_gold.play()
                            elif c['type'] == "TIME_THIEF": # KIRMIZI
                                game.time_left -= 3
                                game.combo = 0
                                if game.sound_boom: game.sound_boom.play()
                            elif c['type'] == "BAD": # YESIL
                                game.combo = 0 # ARTIK CAN GITMIYOR, SADECE COMBO SIFIRLANIYOR
                                if game.sound_boom: game.sound_boom.play()
                            
                            game.circles.remove(c)
                            hit_target = True
                            break
                    if not hit_target: game.combo = 0

        game.update_logic(dt)
        game.draw()
        await asyncio.sleep(0)
        game.clock.tick(60)

if __name__ == "__main__":
    asyncio.run(main())
