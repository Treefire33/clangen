import logging
import os
from copy import copy

import pygame
import ujson

from scripts.special_dates import SpecialDate, is_today
from scripts.game_structure.game_essentials import game
import xml.etree.ElementTree as xml_parser
from xml.etree.ElementTree import Element
import math

logger = logging.getLogger(__name__)


class Sprites:
    cat_tints = {}
    white_patches_tints = {}
    clan_symbols = []

    def __init__(self):
        """Class that handles and hold all spritesheets.
        Size is normally automatically determined by the size
        of the lineart. If a size is passed, it will override
        this value."""
        self.symbol_dict = None
        self.size = None
        self.spritesheets = {}
        self.images = {}
        self.sprites = {}

        # Shared empty sprite for placeholders
        self.blank_sprite = None

        self.load_tints()

    def load_tints(self):
        try:
            with open("sprites/dicts/tint.json", "r", encoding="utf-8") as read_file:
                self.cat_tints = ujson.loads(read_file.read())
        except IOError:
            print("ERROR: Reading Tints")

        try:
            with open(
                "sprites/dicts/white_patches_tint.json", "r", encoding="utf-8"
            ) as read_file:
                self.white_patches_tints = ujson.loads(read_file.read())
        except IOError:
            print("ERROR: Reading White Patches Tints")

    def spritesheet(self, a_file, name):
        """
        Add spritesheet called name from a_file.

        Parameters:
        a_file -- Path to the file to create a spritesheet from.
        name -- Name to call the new spritesheet.
        """
        self.spritesheets[name] = pygame.image.load(a_file).convert_alpha()

    def make_group(
        self, spritesheet, pos, name, sprites_x=3, sprites_y=7, no_index=False
    ):  # pos = ex. (2, 3), no single pixels
        """
        Divide sprites on a spritesheet into groups of sprites that are easily accessible
        :param spritesheet: Name of spritesheet file
        :param pos: (x,y) tuple of offsets. NOT pixel offset, but offset of other sprites
        :param name: Name of group being made
        :param sprites_x: default 3, number of sprites horizontally
        :param sprites_y: default 3, number of sprites vertically
        :param no_index: default False, set True if sprite name does not require cat pose index
        """

        group_x_ofs = pos[0] * sprites_x * self.size
        group_y_ofs = pos[1] * sprites_y * self.size
        i = 0

        # splitting group into singular sprites and storing into self.sprites section
        for y in range(sprites_y):
            for x in range(sprites_x):
                if no_index:
                    full_name = f"{name}"
                else:
                    full_name = f"{name}{i}"

                try:
                    new_sprite = pygame.Surface.subsurface(
                        self.spritesheets[spritesheet],
                        group_x_ofs + x * self.size,
                        group_y_ofs + y * self.size,
                        self.size,
                        self.size,
                    )

                except ValueError:
                    # Fallback for non-existent sprites
                    print(f"WARNING: nonexistent sprite - {full_name}")
                    if not self.blank_sprite:
                        self.blank_sprite = pygame.Surface(
                            (self.size, self.size), pygame.HWSURFACE | pygame.SRCALPHA
                        )
                    new_sprite = self.blank_sprite

                self.sprites[full_name] = new_sprite
                i += 1

    def load_all(self):
        # get the width and height of the spritesheet
        lineart = pygame.image.load("sprites/lineart/lineart.png")
        width, height = lineart.get_size()
        del lineart  # unneeded

        # if anyone changes lineart for whatever reason update this
        if isinstance(self.size, int):
            pass
        elif width / 3 == height / 7:
            self.size = width / 3
        else:
            self.size = 50  # default, what base clangen uses
            print(f"lineart.png is not 3x7, falling back to {self.size}")
            print(
                f"if you are a modder, please update scripts/cat/sprites.py and "
                f"do a search for 'if width / 3 == height / 7:'"
            )

        del width, height  # unneeded

        self.spritesheet("sprites/symbols.png", "symbols")

        self.load_sprites()
        self.load_symbols()

    def load_sprites(self):
        for x in (
            "lineart",
            "colours",
            "accessories",
            "pelts",
            "misc"
        ):
            cur_path = f"sprites/{x}"
            if not os.path.exists(f"{cur_path}/sprites.xml"):
                print(f"Required sprite path ({x}) was missing sprites.xml.")
                continue

            spritesheets = xml_parser.parse(f"{cur_path}/sprites.xml").getroot()

            for spritesheet in spritesheets.iter("spritesheet"):
                image = spritesheet.get("image")

                self.spritesheet(f"{cur_path}/{spritesheet.get("image")}.png", image)

                self.parse_groups(spritesheets, spritesheet)

    def parse_groups(self, root: Element, spritesheet: Element):
        image = spritesheet.get("image")
        name_type = spritesheet.get("name_convention", None)
        affix = spritesheet.get("affix", None)
        prototype_name = spritesheet.get("prototype", "")
        prototype_affix = spritesheet.get("prototype_affix", "")

        prototype = root.find(f'.//spritesheet_prototype[@name="{prototype_name}"]')

        cols = math.floor(self.spritesheets[image].width / (self.size * 3))

        x = 0
        y = 0
        for group in (prototype or spritesheet).iter("sprite_group"):
            name = group.get("name") + (prototype_affix if prototype else "")
            coord = group.get("coordinate", None)
            if coord:
                coord = coord.split(' ')
                x = int(coord[0])
                y = int(coord[1])

            group_name = self.adjust_group_name(name, name_type, affix or image)

            self.make_group(image, (x, y), group_name)
            x += 1
            if x >= cols:
                y += 1
                x = 0

    def adjust_group_name(
        self,
        name: str,
        convention: str,
        affix: str = None
    ) -> str:
        match convention:
            case "prefix":
                return affix+name
            case "suffix":
                return name+affix
            case "colours":
                return affix[:-7]+name
            case None:
                return name

    def load_symbols(self):
        """
        loads clan symbols
        """

        if os.path.exists("resources/dicts/clan_symbols.json"):
            with open(
                "resources/dicts/clan_symbols.json", encoding="utf-8"
            ) as read_file:
                self.symbol_dict = ujson.loads(read_file.read())

        # U and X omitted from letter list due to having no prefixes
        letters = [
            "A",
            "B",
            "C",
            "D",
            "E",
            "F",
            "G",
            "H",
            "I",
            "J",
            "K",
            "L",
            "M",
            "N",
            "O",
            "P",
            "Q",
            "R",
            "S",
            "T",
            "V",
            "W",
            "Y",
            "Z",
        ]

        # sprite names will format as "symbol{PREFIX}{INDEX}", ex. "symbolSPRING0"
        y_pos = 1
        for letter in letters:
            x_mod = 0
            for i, symbol in enumerate(
                [
                    symbol
                    for symbol in self.symbol_dict
                    if letter in symbol and self.symbol_dict[symbol]["variants"]
                ]
            ):
                if self.symbol_dict[symbol]["variants"] > 1 and x_mod > 0:
                    x_mod += -1
                for variant_index in range(self.symbol_dict[symbol]["variants"]):
                    x_pos = i + x_mod

                    if self.symbol_dict[symbol]["variants"] > 1:
                        x_mod += 1
                    elif x_mod > 0:
                        x_pos += -1

                    self.clan_symbols.append(f"symbol{symbol.upper()}{variant_index}")
                    self.make_group(
                        "symbols",
                        (x_pos, y_pos),
                        f"symbol{symbol.upper()}{variant_index}",
                        sprites_x=1,
                        sprites_y=1,
                        no_index=True,
                    )

            y_pos += 1

    def get_symbol(self, symbol: str, force_light=False):
        """Change the color of the symbol to match the requested theme, then return it
        :param Surface symbol: The clan symbol to convert
        :param force_light: Use to ignore dark mode and always display the light mode color
        """
        symbol = self.sprites.get(symbol)
        if symbol is None:
            logger.warning("%s is not a known Clan symbol! Using default.")
            symbol = self.sprites[self.clan_symbols[0]]

        recolored_symbol = copy(symbol)
        var = pygame.PixelArray(recolored_symbol)
        var.replace(
            (87, 76, 45),
            (
                pygame.Color(game.config["theme"]["dark_mode_clan_symbols"])
                if not force_light and game.settings["dark mode"]
                else pygame.Color(game.config["theme"]["light_mode_clan_symbols"])
            ),
            distance=0,
        )
        del var

        return recolored_symbol


# CREATE INSTANCE
sprites = Sprites()
