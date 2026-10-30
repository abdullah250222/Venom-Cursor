import pygame
from .config import BACKGROUND, GRID_SPACING, GRID_OFFSET, DOT_RADIUS, DOT_DIM

_cache = {"size": None, "surf": None}


def _build(size):
    w, h = size
    surf = pygame.Surface(size)
    surf.fill(BACKGROUND) 
    for x in range(GRID_OFFSET, w, GRID_SPACING):
        for y in range(GRID_OFFSET, h, GRID_SPACING):
            pygame.draw.circle(surf, DOT_DIM, (x, y), DOT_RADIUS)
    return surf


def draw_background(surface):
    size = surface.get_size()
    if _cache["size"] != size:
        _cache["size"] = size
        _cache["surf"] = _build(size)
    surface.blit(_cache["surf"], (0, 0))