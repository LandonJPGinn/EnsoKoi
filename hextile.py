from typing import Optional
from dataclasses import dataclass
from dataclasses import field
from itertools import product
from collections import namedtuple
from collections import defaultdict
import math
import random
import string
import json


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

    def __init__(self):
        self.InitializePlayers()

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

    @classmethod
    def arrangePieces(cls, player):
        print(player.team.koi)


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

    @property
    def koi(self):
        return (
            Tancho("TanchoA"),
            Tancho("TanchoB"),
            Tancho("TanchoC"),
            Tancho("TanchoD"),
            Asagi("AsagiA"),
            Asagi("AsagiB"),
            Kumonryu("KumonryuA"),
            Kumonryu("KumonryuB"),
            Utsuri("UtsuriA"),
            Utsuri("UtsuriB"),
            Ogon("OgonA"),
            Ogon("OgonB"),
            Sumi("Sumi"),
        )

    @property
    def stones(self):
        return (
            Stone("StoneA"),
            Stone("StoneB"),
            Stone("StoneC"),
            Stone("StoneD"),
            Stone("StoneE"),
        )

    @property
    def lotustiles(self):
        return (
            Tile_Lotus("LotusA"),
            Tile_Lotus("LotusB"),
            Tile_Lotus("LotusC"),
            Tile_Lotus("LotusD"),
            Tile_Lotus("LotusE"),
            Tile_Lotus("LotusF"),
            Tile_Lotus("LotusG"),
            Tile_Lotus("LotusH"),
            Tile_Lotus("LotusI"),
        )


class Player:

    def __init__(self, name=""):
        self._order = None
        self.player_name = name
        self.score = 0
        self.team = InitialTeam()
        self.captured = {}
        self.stones = []


# Exceptions
class BoundaryException(Exception):pass









# Runtime Test Code







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

a = Coord((0, 0, 1))
b = Coord((2, -2, 4))
c = Coord((12, 2, -3))

print(f'{a!s:_^120}')

M = Map()



for _ in M.notation.items():
    print(_)



print(M.notation.get("H3"))
print("//")
print(M.notation_map.get("A2"))


h = HexTile(coord=M.notation.get("H7"))
print(repr(h))
print(h.up)
print(h.inBounds)


print(h.neighbors)


for ne in h.neighbors:
    address = M.address(ne)
    print(f"neighbor at {ne} is called {address}")
    print("who is at position:")
    print(M.position(address))
    safe = M.isSafe(address)
    print(f"{address} is safe? {safe}")



# perm = {
#     p: Coord(p)
#     for p
#     in list(permutations(range(-1 * Map.max_radius, Map.max_radius + 1), 3))
#     if sum(p) == 0
# }
# perm[Rules.origin] = Coord(Rules.origin)



# for x in perm.items():
#     print(x)

# print(len(perm))

# print((7*6)+(6*6)+(5*6)+(4*6)+(3*6)+(2*6)+(1*6)+1)

# def corners(axis):
#     return abs(axis) >= Map.max_radius - 1


# unsafe = [y for y in perm if len([x for x in map(corners, y) if x]) == 2]

# print(unsafe)
# print(len(unsafe))
# print(4*6)





myPlayer = Player(name="Landon")



placement = {
    2: {
        "P1": {
            "TanchoA": "F4",
            "TanchoB": "G5",
            "TanchoC": "I5",
            "TanchoD": "J4",
            "AsagiA": "H2",
            "AsagiB": "H5",
            "KumonryuA": "G3",
            "KumonryuB": "I3",
            "UtsuriA": "D2",
            "UtsuriB": "L2",
            "OgonA": "F2",
            "OgonB": "J2",
            "Sumi": "H1",
        },
        "P2": {
            "TanchoA": "J10",
            "TanchoB": "I10",
            "TanchoC": "G10",
            "TanchoD": "F10",
            "AsagiA": "H14",
            "AsagiB": "H11",
            "KumonryuA": "I12",
            "KumonryuB": "G12",
            "UtsuriA": "L10",
            "UtsuriB": "D10",
            "OgonA": "J12",
            "OgonB": "F12",
            "Sumi": "H15",
        },
    },
    3: {
        "P1": {
            "Sumi": "",
        },
        "P2": {
            "Sumi": "",
        },
        "P3": {
            "Sumi": "",
        },
    },
    4: {
        "P1": {
            "Sumi": "",
        },
        "P2": {
            "Sumi": "",
        },
        "P3": {
            "Sumi": "",
        },
        "P4": {
            "Sumi": "",
        },
    },
    5: {
        "P1": {
            "Sumi": "",
        },
        "P2": {
            "Sumi": "",
        },
        "P3": {
            "Sumi": "",
        },
        "P4": {
            "Sumi": "",
        },
        "P5": {
            "Sumi": "",
        },
    },
    6: {
        "P1": {
            "Sumi": "",
        },
        "P2": {
            "Sumi": "",
        },
        "P3": {
            "Sumi": "",
        },
        "P4": {
            "Sumi": "",
        },
        "P5": {
            "Sumi": "",
        },
        "P6": {
            "Sumi": "",
        },
    },
}


