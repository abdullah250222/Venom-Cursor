import pygame
import sys

from .config import FPS, WINDOW_SIZE
from .rendering import draw_background
from .tendrils import VenomCreature


class VenomApp:
    def __init__(self):
        pygame.init()

        pygame.display.set_caption("Venom Mouse Tracker")

        self.screen = pygame.display.set_mode(
            WINDOW_SIZE,
            pygame.RESIZABLE,
        )

        self.clock = pygame.time.Clock()

        self.width, self.height = self.screen.get_size()

        self.running = True

        self.venom = VenomCreature(
            self.width,
            self.height,
        )

        self.previous_mouse = pygame.mouse.get_pos()
        self.last_mouse_move = 0.0

        self.font = pygame.font.SysFont(
            "consolas",
            14,
        )

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                self.venom.provoke(event.pos)

            elif event.type == pygame.VIDEORESIZE:
                self.width = event.w
                self.height = event.h

                self.screen = pygame.display.set_mode(
                    (self.width, self.height),
                    pygame.RESIZABLE,
                )

                self.venom.width = self.width
                self.venom.height = self.height

    def run(self):
        while self.running:
            dt = min(
                self.clock.tick(FPS) / 1000.0,
                0.033,
            )

            self.handle_events()

            mouse = pygame.mouse.get_pos()
            self.venom.holding = pygame.mouse.get_pressed()[0]

            if mouse != self.previous_mouse:
                self.last_mouse_move = pygame.time.get_ticks() / 1000.0

            self.previous_mouse = mouse

            now = pygame.time.get_ticks() / 1000.0

            chasing = (now - self.last_mouse_move) < 3.0

            self.venom.update(
                dt,
                mouse,
                chasing,
            )

            draw_background(self.screen)

    
            self.venom.draw(self.screen)

            pygame.display.flip()

        pygame.quit()
        sys.exit(0)


def main():
    app = VenomApp()
    app.run()