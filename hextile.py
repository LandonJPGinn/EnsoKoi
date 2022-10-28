import json
import math
import random
import string
from collections import defaultdict, namedtuple
from dataclasses import dataclass, field
from itertools import product
from typing import Optional

from config import Loader


class Rules:
    max_radius: int = 7
    origin = (0,0,0)
    up = (1,0,-1)
    upright = (0,1,-1)
    downright = (-1,1,0)
    down = (-1,0,1)
    downleft = (0,-1,1)
    upleft = (1,-1,0)

    def width(self, val):
        return val * math.sqr(3)

    def height(self, val):
        return val * 2

    def width_space(self):
        return self.width

    def height_space(self):
        return self.height * .75


class EnsoKoi:
    instance = None

    def __new__(cls):
        if cls.instance:
            return cls.instance
        cls.instance = super().__new__(cls)
        return cls.instance

    def __init__(self):
        self.map = Map()
        self.player_count = 2
        self.positions = Loader.initial_positions(self.player_count)
        self.boardtiles = {self.map.address(cd): HexTile(cd) for cd in self.map.tiles.values()}
        self.initializePlayers()
        self.startingPositions()

    def initializePlayers(self, playerNameA="Black", playerNameB="Red"):
        self.players = {
            "P1": Player(name=playerNameA),
            "P2": Player(name=playerNameB)
        }
        self.shuffleOrder()

    def shuffleOrder(self):
        v = random.randint(0,1)
        for pl in self.players.values():
            pl._order = f"P{v+1}"
            v ^= 1

    def swapOrder(self):
        for pl in self.players.values():
            v = int(pl._order[-1])
            v ^= 1
            pl._order = f"P{v+1}"

    def startingPositions(self):
        for p in self.players.values():
            self.arrangePieces(p)

    def arrangePieces(self, player):
        key = player._order
        for k, tile in self.positions.get(key).items():
            t = string.Template(k)
            koiname = t.safe_substitute(Name=player.player_name)
            _koi = player.team.get(koiname)
            self.boardtiles.get(tile).occupant.append(_koi)


class Coord(tuple):
    def __init__(self, pos):
        self._coord = pos
        self.s, self.q, self.r = pos

    def __iter__(self):
        yield from self._coord

    def __add__(self, val):
        # self._coord = tuple(map(sum, zip(self._coord, val)))
        return Coord(tuple(map(sum, zip(self._coord, val))))

    def __sub__(self, val):
        inverse_val = (x * -1 for x in val)
        return Coord(tuple(map(sum, zip(self._coord, val))))

    def __truediv__(self, target):
        sub = self.__sub__(target)
        return max(abs(sub.s), abs(sub.q), abs(sub.r))

    def __str__(self):
        return str(self._coord)

    # def __repr__(self):
    #     return f"{self.__class__} Object at {self._coord}"


class IterProperty:
    def __init__(self, func):
        self.func = func

    def __get__(self, inst, cls):
        return self.func(cls)


class Map:
    instance = None
    def __new__(cls):
        if cls.instance:
            return cls.instance
        cls.instance = super().__new__(cls)
        return cls.instance

    def __init__(self):
        self.notation_map = Map.notation
        self.inverted_notation_map = {v:k for k, v in self.notation_map.items()}

    @IterProperty
    def tiles(cls):
        tiles = {
            p: Coord(p)
            for p
            in list(product(range(-1 * Rules.max_radius, Rules.max_radius + 1), repeat=3))
            if sum(p) == 0
        }
        tiles[Rules.origin] = Coord(Rules.origin)
        return dict(sorted(tiles.items(), key=lambda x: x[1][1]))

    @IterProperty
    def unsafe_tiles(cls):
        return [
            y
            for y
            in cls.tiles
            if len([x for x in map(Map.corner_range, y) if x])
            == 2
        ]

    @classmethod
    def corner_range(cls, axis):
        return abs(axis) >= Rules.max_radius - 1

    @IterProperty
    def notation(self):
        columns = defaultdict(list)
        _notation = {}

        for e in Map.tiles.values():
            columnidx = e.q + Rules.max_radius
            col = string.ascii_uppercase[columnidx]
            columns[col].append(e)

        for cc, v in columns.items():
            row = 1
            for grid in v:
                _notation[f"{cc}{row}"] = grid
                #print(f"{cc}{row}: Is the Grid located at {grid}")
                row += 1

        return _notation

    def address(self, position):
        return self.inverted_notation_map.get(position)

    def position(self, address):
        return self.notation_map.get(address)

    def isSafe(self, tile):
        if isinstance(tile, Coord):
            return tile not in Map.unsafe_tiles
        if isinstance(tile, str) and tile in Map.notation.keys():
            return self.position(tile) not in Map.unsafe_tiles


@dataclass
class HexTile:

    def __init__(self, coord):

        # if coord not in Map.tiles:
        #     raise BoundaryException

        self.coord = Coord(coord)
        self.occupant = []
        self.lotus = []
        self.safe = self.coord not in Map.unsafe_tiles
        self.inBounds = self.coord in Map.tiles

    def __str__(self):
        return str(self.coord)

    def __repr__(self):
        return f"{self.__class__}: -->  {self.coord!r}\n{' ' * len(str(self.__class__))}  --> Occupant: {self.occupant}"

    @property
    def up(self):
        return tuple(self.coord + Coord(Rules.up))

    @property
    def upright(self):
        return tuple(self.coord + Coord(Rules.upright))

    @property
    def downright(self):
        return tuple(self.coord + Coord(Rules.downright))

    @property
    def down(self):
        return tuple(self.coord + Coord(Rules.down))

    @property
    def downleft(self):
        return tuple(self.coord + Coord(Rules.downleft))

    @property
    def upleft(self):
        return tuple(self.coord + Coord(Rules.upleft))

    @property
    def neighbors(self):
        return (
            self.up,
            self.upright,
            self.downright,
            self.down,
            self.downleft,
            self.upleft
        )

    def kill_occupant(self):
        self.occupant = []


Piece = namedtuple("Piece",["id", "range", "value", "type", "position", "active"])
Piece.__doc__ += ": Enso Koi Game Piece"
Piece.id.__doc__ = "Identifier of Game Piece"
Piece.range.__doc__ = "Maximum number of moveable spaces"
Piece.value.__doc__ = "Point value for captured Game Piece"
Piece.type.__doc__ = "Classification of Game Piece"
Piece.position.__doc__ = "Position of Game Piece on the Board"
Piece.active.__doc__ = "Game Piece is live on the board"

KoiPiece = namedtuple("Koi", Piece._fields + ("multi", "jumps", "canStone", "canLotus", "flipped"))
KoiPiece.__doc__ += ": Playable Koi Piece"
KoiPiece.multi.__doc__ = "Is Koi multi-directional: bool"
KoiPiece.jumps.__doc__ = "Maximum number of jumps: 1 | 2"
KoiPiece.canStone.__doc__ = "Is Koi able to jump stones: bool"
KoiPiece.canLotus.__doc__ = "Is Koi able to capture White Lotus: bool"
KoiPiece.flipped.__doc__ = "Is Koi in flipped position: bool"


# Board Pieces
Stone       = lambda name: Piece(id=name, range=0, value=0.5, type="Stone", position=None, active=False)
White_Lotus = lambda name: Piece(id=name, range=0, value=5, type="WhiteLotus", position=None, active=False)
Tile_Lotus  = lambda name: Piece(id=name, range=0, value=0, type="Lotus", position=None, active=False)

# Player Pieces
Tancho      = lambda name: KoiPiece(id=name, range=2, value=1, type="Koi", multi=False, jumps=2, canStone=False, canLotus=False, position=None, active=False, flipped=False)
Asagi       = lambda name: KoiPiece(id=name, range=3, value=1, type="Koi", multi=False, jumps=1, canStone=True, canLotus=False, position=None, active=False, flipped=False)
Kumonryu    = lambda name: KoiPiece(id=name, range=4, value=1, type="Koi", multi=False, jumps=1, canStone=False, canLotus=True, position=None, active=False, flipped=False)
Utsuri      = lambda name: KoiPiece(id=name, range=2, value=2, type="Koi", multi=True, jumps=2, canStone=False, canLotus=False, position=None, active=False, flipped=False)
Ogon        = lambda name: KoiPiece(id=name, range=3, value=2, type="Koi", multi=True, jumps=1, canStone=True, canLotus=False, position=None, active=False, flipped=False)
Sumi        = lambda name: KoiPiece(id=name, range=4, value=2, type="Koi", multi=True, jumps=1, canStone=False, canLotus=True, position=None, active=False, flipped=False)
# Rules unclear regarding white lotus and lotus tiles
# Rules unclear on how to setup



class InitialTeam:
    def __init__(self, name):
        self.name = name

    @property
    def koi(self):
        return {
            f"{self.name}_TanchoA": Tancho(f"{self.name}_TanchoA"),
            f"{self.name}_TanchoB": Tancho(f"{self.name}_TanchoB"),
            f"{self.name}_TanchoC": Tancho(f"{self.name}_TanchoC"),
            f"{self.name}_TanchoD": Tancho(f"{self.name}_TanchoD"),
            f"{self.name}_AsagiA": Asagi(f"{self.name}_AsagiA"),
            f"{self.name}_AsagiB": Asagi(f"{self.name}_AsagiB"),
            f"{self.name}_KumonryuA": Kumonryu(f"{self.name}_KumonryuA"),
            f"{self.name}_KumonryuB": Kumonryu(f"{self.name}_KumonryuB"),
            f"{self.name}_UtsuriA": Utsuri(f"{self.name}_UtsuriA"),
            f"{self.name}_UtsuriB": Utsuri(f"{self.name}_UtsuriB"),
            f"{self.name}_OgonA": Ogon(f"{self.name}_OgonA"),
            f"{self.name}_OgonB": Ogon(f"{self.name}_OgonB"),
            f"{self.name}_Sumi": Sumi(f"{self.name}_Sumi"),
        }

    @property
    def stones(self):
        return {
            f"{self.name}_StoneA": Stone(f"{self.name}_StoneA"),
            f"{self.name}_StoneB": Stone(f"{self.name}_StoneB"),
            f"{self.name}_StoneC": Stone(f"{self.name}_StoneC"),
            f"{self.name}_StoneD": Stone(f"{self.name}_StoneD"),
            f"{self.name}_StoneE": Stone(f"{self.name}_StoneE"),
        }

    @property
    def lotustiles(self):
        return {
            f"{self.name}_LotusA": Tile_Lotus(f"{self.name}_LotusA"),
            f"{self.name}_LotusB": Tile_Lotus(f"{self.name}_LotusB"),
            f"{self.name}_LotusC": Tile_Lotus(f"{self.name}_LotusC"),
            f"{self.name}_LotusD": Tile_Lotus(f"{self.name}_LotusD"),
            f"{self.name}_LotusE": Tile_Lotus(f"{self.name}_LotusE"),
            f"{self.name}_LotusF": Tile_Lotus(f"{self.name}_LotusF"),
            f"{self.name}_LotusG": Tile_Lotus(f"{self.name}_LotusG"),
            f"{self.name}_LotusH": Tile_Lotus(f"{self.name}_LotusH"),
            f"{self.name}_LotusI": Tile_Lotus(f"{self.name}_LotusI"),
        }


class Player:

    def __init__(self, name=""):
        self.player_name = name
        self._order = None
        self._initialteam = InitialTeam(self.player_name)
        self.score = 0
        self.team = self._initialteam.koi
        self.captured = {}
        self.stones = self._initialteam.stones
        self.lotustiles = self._initialteam.lotustiles


# Exceptions
class BoundaryException(Exception):pass





# Runtime Test Code
instance = EnsoKoi()



for hx in instance.boardtiles.items():
    print(f"{hx!r}")


# q ascending == Letter
# s += Number along letter

"""
sqrt(dq² + dr² + dq*dr)


A Hex direction should be predictable

0 deg       up
60 deg      upright
120 deg     downright
180 deg     down
240 deg     downleft
300 deg     upleft

"""



# Maybe logic for movement
# for ne in h.neighbors:
#     address = M.address(ne)
#     print(f"neighbor at {ne} is called {address}")
#     # print("who is at position:")
#     # print(M.position(address))
#     safe = M.isSafe(address)
#     if safe:
#         print(f"\t\t{address} is safe? {safe}")



# Todo:
"""
Clarify Lotus tile rules
- There are x amount of lotus tiles that are shuffled and placed face down in the center of the map at random
    True Blind Random
- Players take turns placing lotus tiles face down at the start
    Strategic Blind Random
- Players take turns designating a tile to be a lotus at the start
    Strategic Visible Random
- The board has set lotus tiles
    Strategic

Game loop
break into phases
initial placement setup
initial player setup
player plays
other player plays
loop until conditions met
conclusive phase
rematch menu


"""
