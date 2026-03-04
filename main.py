# -*- coding: utf-8 -*-
import pygame
import random
import sys
import asyncio  # Web uyumlulugu icin kritik

# --- AYARLAR VE RENKLER ---
WIDTH, HEIGHT = 800, 600
WHITE = (255, 255, 255)
BLUE = (50, 150, 255)
GREEN = (50, 255, 50)
RED = (255, 50, 50)
DARK_BG = (20, 20, 30)
BLACK = (0, 0, 0)


class Particle:
    """Tiklama aninda olusacak patlama halkasi efekti"""

    def __init__(self, pos, color):
        self.pos = pos
        self.color = color
        self.radius = 10
        self.alpha = 255
        self.dead = False

    def update(self):
        self.radius += 5
        self.alpha -= 15
        if self.alpha <= 0:
            self.dead = True

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
        pygame.display.set_caption("Refleks Oyunu")

        # SESLERI YUKLE
        try:
            self.sound_glup = pygame.mixer.Sound("glup.ogg")
            self.sound_boom = pygame.mixer.Sound("explosion.ogg")
        except:
            self.sound_glup = self.sound_boom = None

        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 24, bold=True)
        self.big_font = pygame.font.SysFont("Arial", 50, bold=True)
        self.reset_game()

    def reset_game(self):
        self.score = 0
        self.lives = 3
        self.level = 1
        self.circles = []
        self.particles = []
        self.spawn_timer = 0
        self.game_over = False
        self.base_duration = 1500

    def spawn_circle(self):
        x = random.randint(50, WIDTH - 50)
        y = random.randint(50, HEIGHT - 50)
        color = GREEN if random.random() < 0.2 else BLUE
        self.circles.append({
            'pos': (x, y),
            'color': color,
            'time': pygame.time.get_ticks()
        })

    def update_logic(self):
        if self.game_over:
            return

        current_time = pygame.time.get_ticks()
        self.level = (self.score // 150) + 1
        current_duration = max(400, self.base_duration - (self.level - 1) * 150)
        spawn_speed = max(350, 1000 - (self.level * 60))

        if current_time - self.spawn_timer > spawn_speed:
            self.spawn_circle()
            self.spawn_timer = current_time

        self.circles = [c for c in self.circles if current_time - c['time'] < current_duration]

        for p in self.particles[:]:
            p.update()
            if p.dead:
                self.particles.remove(p)

        if self.lives <= 0:
            self.game_over = True

    def draw(self):
        self.screen.fill(DARK_BG)

        score_surf = self.font.render(f"PUAN: {self.score}", True, WHITE)
        level_surf = self.font.render(f"LEVEL: {self.level}", True, WHITE)
        lives_surf = self.font.render(f"CAN: {self.lives}", True, RED)

        self.screen.blit(score_surf, (20, 20))
        self.screen.blit(level_surf, (WIDTH // 2 - 50, 20))
        self.screen.blit(lives_surf, (WIDTH - 150, 20))

        for circle in self.circles:
            pygame.draw.circle(self.screen, circle['color'], circle['pos'], 25)
            pygame.draw.circle(self.screen, WHITE, circle['pos'], 25, 2)

        for p in self.particles:
            p.draw(self.screen)

        if self.game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            self.screen.blit(overlay, (0, 0))

            go_text = self.big_font.render("OYUN BITTI", True, RED)
            restart_text = self.font.render("Yeniden baslatmak icin 'R' tusuna bas", True, WHITE)
            self.screen.blit(go_text, (WIDTH // 2 - 150, HEIGHT // 2 - 50))
            self.screen.blit(restart_text, (WIDTH // 2 - 200, HEIGHT // 2 + 50))

        pygame.display.flip()


# --- WEB UYUMLU ANA DONGU ---
async def main():
    game = CircleGame()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r and game.game_over:
                    game.reset_game()

            if event.type == pygame.MOUSEBUTTONDOWN and not game.game_over:
                mouse_pos = event.pos
                for circle in game.circles[:]:
                    dx = circle['pos'][0] - mouse_pos[0]
                    dy = circle['pos'][1] - mouse_pos[1]
                    if (dx ** 2 + dy ** 2) ** 0.5 < 25:
                        game.particles.append(Particle(circle['pos'], circle['color']))
                        if circle['color'] == BLUE:
                            game.score += 10
                            if game.sound_glup: game.sound_glup.play()
                        elif circle['color'] == GREEN:
                            game.lives -= 1
                            if game.sound_boom: game.sound_boom.play()
                        game.circles.remove(circle)
                        break

        game.update_logic()
        game.draw()

        # Bu satir pygbag'in tarayicida donmadan calismasini saglar
        await asyncio.sleep(0)
        game.clock.tick(60)


if __name__ == "__main__":
    asyncio.run(main())