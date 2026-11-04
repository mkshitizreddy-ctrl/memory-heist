import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from core import hero_sprites as hs
from core.hero_sprites import HEROES, make_hero_frames


@pytest.fixture(autouse=True)
def display():
    pygame.init()
    pygame.display.set_mode((100, 100))


def raw(surface):
    return pygame.image.tostring(surface, "RGBA")


@pytest.mark.parametrize("name", HEROES)
def test_frames_have_the_shape_player_expects(name):
    f = make_hero_frames(name)
    assert set(f) == {"idle", "walk", "blink"} and len(f["walk"]) == 4
    for img in [f["idle"]] + f["walk"]:
        assert img.get_size() == (32, 32)


@pytest.mark.parametrize("name", HEROES)
def test_transparent_background_and_outlined_silhouette(name):
    img = make_hero_frames(name)["idle"]
    assert img.get_at((0, 0))[3] == 0 and img.get_at((31, 31))[3] == 0
    opaque = [(x, y) for x in range(32) for y in range(32) if img.get_at((x, y))[3] == 255]
    assert len(opaque) > 250
    assert hs.OUTLINE[:3] in [tuple(img.get_at(p))[:3] for p in opaque]


@pytest.mark.parametrize("name", HEROES)
def test_source_art_leaves_room_for_the_outline(name):
    head, body, legs = hs._PARTS[name]
    for key, leg_rows in legs.items():
        rows = head + body + leg_rows
        assert len(rows) <= hs.GRID - 1                 # a free row for the outline
        assert all(len(r) == hs.GRID for r in rows)
        assert set(rows[0]) == {"."}
        assert all(r[0] == "." and r[-1] == "." for r in rows)


@pytest.mark.parametrize("name", HEROES)
def test_walk_cycle_animates_and_returns_to_idle(name):
    f = make_hero_frames(name)
    w = [raw(i) for i in f["walk"]]
    assert w[1] == w[3] == raw(f["idle"])
    assert w[0] != w[1] and w[2] != w[1] and w[0] != w[2]


def test_heroes_are_distinct_and_carry_their_signature_colours():
    g, e = make_hero_frames("ghost")["idle"], make_hero_frames("echo")["idle"]
    assert raw(g) != raw(e)
    def has(img, colour):
        return any(tuple(img.get_at((x, y)))[:3] == colour
                   for x in range(32) for y in range(32))
    assert has(g, hs.PALETTES["ghost"]["V"])          # cyan visor
    assert has(e, hs.PALETTES["echo"]["Y"])           # gold goggles
    assert not has(e, hs.PALETTES["ghost"]["V"])


def test_unknown_hero_rejected():
    with pytest.raises(ValueError, match="unknown hero"):
        make_hero_frames("nobody")


def test_ghost_is_bright_enough_to_read_on_the_navy_floor():
    img = make_hero_frames("ghost")["idle"]
    body = [img.get_at((x, y))[:3] for x in range(32) for y in range(32)
            if img.get_at((x, y))[3] == 255 and img.get_at((x, y))[:3] != hs.OUTLINE[:3]]
    avg = sum(sum(c) / 3 for c in body) / len(body)
    assert avg > 60


def _pixels(img):
    w, h = img.get_size()
    return [tuple(img.get_at((x, y)))[:3] for x in range(w) for y in range(h)
            if img.get_at((x, y))[3] == 255]


def test_ghost_visor_is_really_bright_cyan_and_echo_goggles_really_gold():
    ghost = _pixels(make_hero_frames("ghost")["idle"])
    echo = _pixels(make_hero_frames("echo")["idle"])
    assert any(r < 140 and g > 200 and b > 200 for r, g, b in ghost)
    assert any(r > 230 and 170 < g < 220 and b < 100 for r, g, b in echo)
    assert not any(r < 140 and g > 200 and b > 200 for r, g, b in echo)


def test_ghost_hood_and_coat_are_not_lost_against_a_navy_floor():
    floor = (44, 66, 110)
    for key in ("H", "h", "C", "c", "G"):
        r, g, b = hs.PALETTES["ghost"][key]
        assert (r + g + b) / 3 > 60, key
    img = make_hero_frames("ghost")["idle"]
    # the hood (top of the sprite) must differ clearly from the floor colour
    hood = [p for p in _pixels(img.subsurface((0, 0, 32, 16)))
            if p != hs.OUTLINE[:3] and p != hs.PALETTES["ghost"]["D"]
            and p != hs.PALETTES["ghost"]["V"]]
    assert hood and all(sum(abs(a - b) for a, b in zip(p, floor)) > 25 for p in hood)


# --- wiring ----------------------------------------------------------------
def test_player_uses_hero_sprites_for_story_names_and_old_palettes_still_work():
    from core.player import Player
    from entities.sprites import make_player_frames
    ghost = Player(0, 0, palette="ghost")
    assert raw(ghost.frames["idle"]) == raw(make_hero_frames("ghost")["idle"])
    old = Player(0, 0)                                   # default stays the old cyan
    assert raw(old.frames["idle"]) == raw(make_player_frames("cyan")["idle"])
    assert raw(Player(0, 0, palette="orange").frames["idle"]) == \
        raw(make_player_frames("orange")["idle"])


def test_player_draw_walks_through_the_hero_cycle_and_flips():
    from core.player import Player
    p = Player(10, 10, palette="echo")
    screen = pygame.Surface((100, 100), pygame.SRCALPHA)
    p.draw(screen)
    still = raw(screen)
    p.moving, p.anim_time = True, 0.0                    # walk[0]: the wide-stance frame
    screen2 = pygame.Surface((100, 100), pygame.SRCALPHA)
    p.draw(screen2)
    assert raw(screen2) != still
    p.facing_left = True
    screen3 = pygame.Surface((100, 100), pygame.SRCALPHA)
    p.draw(screen3)
    assert raw(screen3) != raw(screen2)


def test_game_players_are_ghost_and_echo():
    from core.game import Game
    g = Game()
    assert raw(g.player.frames["idle"]) == raw(make_hero_frames("ghost")["idle"])
    assert raw(g.player2.frames["idle"]) == raw(make_hero_frames("echo")["idle"])
    g.music.stop()
    pygame.mixer.stop()
    pygame.mixer.set_reserved(0)


# --- walk bob and shading ---------------------------------------------------
def _eye_row(img, colour):
    return min(y for y in range(img.get_height()) for x in range(img.get_width())
               if tuple(img.get_at((x, y)))[:3] == colour)


@pytest.mark.parametrize("name,key", [("ghost", "V"), ("echo", "Y")])
def test_stride_frames_lift_the_face_one_pixel_and_idle_does_not(name, key):
    frames = make_hero_frames(name)
    colour = hs.PALETTES[name][key]
    idle_row = _eye_row(frames["idle"], colour)
    assert _eye_row(frames["walk"][0], colour) == idle_row - hs.SCALE
    assert _eye_row(frames["walk"][2], colour) == idle_row - hs.SCALE
    assert _eye_row(frames["walk"][1], colour) == idle_row


def test_npc_strides_differ_from_idle_above_the_waist():
    from core.npc_sprites import KINDS, make_npc_frames
    for kind in KINDS:
        frames = make_npc_frames(kind)
        top = lambda img: raw(img.subsurface((0, 0, 32, 20)))
        assert top(frames["walk"][0]) != top(frames["idle"]), kind
        assert top(frames["walk"][1]) == top(frames["idle"]), kind


def test_bob_rows_keeps_the_sprite_the_same_height():
    for head, body in ((hs._GHOST_HEAD, hs._GHOST_BODY), (hs._ECHO_HEAD, hs._ECHO_BODY)):
        assert len(hs.bob_rows(head, body)) == len(head + body)


def test_top_edges_are_lighter_and_undersides_darker_than_the_palette():
    rows = ["....", ".HH.", ".HH.", ".HH.", "...."]
    palette = {"H": (100, 100, 100)}
    top = hs._shaded(rows, 1, 1, "H", palette)
    middle = hs._shaded(rows, 1, 2, "H", palette)
    bottom = hs._shaded(rows, 1, 3, "H", palette)
    side = hs._shaded(rows, 2, 2, "H", palette)
    assert sum(top) > sum(middle) == 300 > sum(side) > sum(bottom)


def test_eyes_and_visors_are_never_shaded():
    rows = ["....", ".V..", "...."]
    assert hs._shaded(rows, 1, 1, "V", {"V": (90, 240, 255)}) == (90, 240, 255)
