#!/usr/bin/env python3
# coding: utf8
import os, enum, random, numpy, pyxel
from abc import ABCMeta, abstractmethod

class App:
    def __init__(self):
        self.__window = Window()
        globals()['Window'] = self.__window
        self.__scene = SceneManager()
        pyxel.run(self.update, self.draw)
    def update(self):
        self.__scene.update()
    def draw(self):
        self.__scene.draw()

class Window:
    def __init__(self):
        pyxel.init(self.Width, self.Height, border_width=self.BorderWidth, caption=self.Caption, fps=60)
    @property
    def Width(self): return 128
    @property
    def Height(self): return 128
    @property
    def Caption(self): return "Ping Pong"
    @property
    def BorderWidth(self): return 0
    def update(self): pass
    def draw(self): pyxel.cls(0)

class SceneType(enum.IntEnum):
    Start = 0
    Play  = 1
    Score = 2

class SceneManager:
    def __init__(self):
        self.__scenes = [StartScene(), PlayScene(), ScoreScene()]
        self.__now = SceneType.Start
    def init(self, *args, **kwargs):
        pass
    def update(self):
        next_scene = self.__scenes[self.__now].update()
        if isinstance(next_scene, SceneType):
            self.__now = next_scene
            self.__scenes[self.__now].init()
        elif isinstance(next_scene, tuple) and isinstance(next_scene[0], SceneType):
            self.__now = next_scene[0]
            if   2 <= len(next_scene): self.__scenes[self.__now].init(*next_scene[1])
            elif 3 <= len(next_scene): self.__scenes[self.__now].init(*next_scene[1], **next_scene[2])
            else:                      self.__scenes[self.__now].init()
    def draw(self):
        self.__scenes[self.__now].draw()

class Scene(metaclass=ABCMeta):
    @abstractmethod
    def init(self, *args, **kwargs): pass
    @abstractmethod
    def update(self): pass
    @abstractmethod
    def draw(self): pass

class StartScene(Scene):
    def __init__(self): pass
    def init(self, *args, **kwargs): pass
    def update(self):
        if pyxel.btn(pyxel.KEY_SPACE):
            return SceneType.Play
    def draw(self):
        pyxel.cls(0)
        pyxel.text(Window.Width // 2 - (4*16/2), Window.Height // 2 - (8*2), 'Push SPACE key !', 7)

class ScoreScene(Scene):
    def __init__(self):
        pass
    def init(self, *args, **kwargs):
        self.__board = Board()
        self.__stone = args[0]
        self.__stones = self.__stone.Stones
        self.__white = numpy.count_nonzero(self.__stones == StoneType.White)
        self.__black = numpy.count_nonzero(self.__stones == StoneType.Black)
    def update(self):
        if pyxel.btn(pyxel.KEY_R):
            return SceneType.Play
    def draw(self):
        pyxel.cls(0)
        self.__board.draw()
        self.__stone.draw()
        x = (Window.Width // 2) - ((8+8*3)//2)
        y = Window.Height // 2 - (8*2//2)
        pyxel.rect(x,         y,       16+4, 16, 4)
        pyxel.circ(x+4,       y+4,     4, 7)
        pyxel.text(x+4+8,     y+2,     str(self.__white), 7)
        pyxel.circ(x+4,       y+4+8,   4, 0)
        pyxel.text(x+4+8,     y+2+8,   str(self.__black), 7)
        pyxel.text((Window.Width // 2) - (4*10//2),     y+2+8+8, 'Push R key', 8)

class PlayScene(Scene):
    def __init__(self):
        self.init()
    def init(self, *args, **kwargs):
        self.__board = Board()
        self.__stone = Stone()
        self.__setter = StoneSetter()
        self.__setter.calc_candidates(self.__stone.Stones)
#        for c in cand: print(c)
    def update(self):
        if self.__setter.is_gameover(self.__stone.Stones):
            print('GameOver!!!!!!!!')
            return SceneType.Score, [self.__stone]
        if self.__setter.update(): # クリック時（石を置いたとき）
            # 自石を置いて敵石をめくる
            self.__stone.set(self.__setter.MousePos[0], self.__setter.MousePos[1], self.__setter.Stone)
            self.__setter.get_reverse_stones(self.__stone.Stones, self.__setter.MousePos[0], self.__setter.MousePos[1])
            for r in self.__setter.Reverses:
                self.__stone.Stones[r[1]][r[0]] = self.__setter.Stone
            # 次のターン
            self.__setter.next_turn()
            self.__setter.calc_candidates(self.__stone.Stones)
            while 0 == len(self.__setter.Candidates):
                self.__setter.next_turn()
                self.__setter.calc_candidates(self.__stone.Stones)
                if 2 <= self.__setter.PassCount: return SceneType.Score, [self.__stone]

    def draw(self):
        pyxel.cls(0)
        self.__board.draw()
        self.__stone.draw()
        self.__setter.draw()
        
class Board:
    TileSize = 16
    TileNum = 8
    Color = 11
    def __init__(self):
        self.__tile_size = 16
        self.__tile_num = 8
    def update(self):
        pass
    def draw(self):
        pyxel.rect(0, 0, Board.TileSize * Board.TileNum, Board.TileSize * Board.TileNum, 11)
        for x in range(Board.TileNum):
            pyxel.line(Board.TileSize * x, 0, Board.TileSize * x, Board.TileSize * Board.TileNum, 5)
        for y in range(Board.TileNum):
            pyxel.line(0, Board.TileSize * y, Board.TileSize * Board.TileNum, Board.TileSize * y, 5)

# https://stackoverflow.com/questions/38773832/is-it-possible-to-add-a-value-named-none-to-enum-type
StoneType  = enum.IntEnum("StoneType", "None White Black")
#class StoneType(enum.IntEnum):
#    None = 0
#    White = 1
#    Black = 1
#StoneType = enum.IntEnum('StoneType', {'None':0, 'White':1, 'Black':2})
class Stone:
    def __init__(self):
        self.__r = Board.TileSize // 2
        self.init()
    def init(self, *args, **kwargs):
        self.__stones = numpy.zeros((Board.TileNum, Board.TileNum))
        self.__stones[3][3] = StoneType.White
        self.__stones[3][4] = StoneType.Black
        self.__stones[4][3] = StoneType.Black
        self.__stones[4][4] = StoneType.White
    @property
    def R(self): return self.__r
    @property
    def Stones(self): return self.__stones
    def set(self, x, y, stone):
        if not isinstance(stone, StoneType): raise Exception('stones should be StoneType.')
        self.__stones[y][x] = stone
        print('set!', x, y, stone)
    def update(self):
        pass
    def draw(self):
        for y in range(Board.TileNum):
            for x in range(Board.TileNum):
                if self.__stones[y][x] == 0: continue
                pyxel.circ(x * Board.TileSize + self.R, y * Board.TileSize + self.R, self.R, self.__get_color(self.__stones[y][x]))
    def __get_color(self, stone):
        if   stone == StoneType.White: return 7
        elif stone == StoneType.Black: return 0


class StoneSetter:
    def __init__(self):
        pyxel.mouse(True)
        self.__stone = StoneType.White
        self.__candidates = [] # 石を置けるマスの候補（マス座標）
        self.__reverses = [] # めくる敵石（マス座標）
        self.__pass_count = 0
        self.__mouse_pos = [0, 0]
        self.__flash_wait = 60
    @property
    def Candidates(self): return self.__candidates
    @property
    def MousePos(self): return self.__mouse_pos 
    @property
    def Stone(self): return self.__stone
    @property
    def Reverses(self): return self.__reverses
    @property
    def PassCount(self): return self.__pass_count
    def next_turn(self):
        self.__stone = StoneType.Black if self.__stone == StoneType.White else StoneType.White
    def calc_candidates(self, stones):
        self.__candidates.clear()
        for y in range(Board.TileNum):
            for x in range(Board.TileNum):
                if 0 != stones[y][x]: continue
                for a in self.get_adjacents():
                    if self.in_board(x, y, a):
#                        print(x, y, a)
                        if self.is_enemy_stone(stones[(y+a[1])][(x+a[0])]): # 隣が敵石である
                            if self.exist_my_stone(stones, x, y, a): # 敵石をはさんだ位置に自石がある
                                self.__candidates.append((x, y))
        print('cand', self.__stone, self.__candidates)
        # 候補がなければパス。両者パスなら終局
        if 0 == len(self.__candidates): self.__pass_count += 1
        else: self.__pass_count = 0
        return self.__candidates
    def get_adjacents(self): # 隣接マスのうち敵石があるマスの方向を取得する[[0, 1, 2][3, 4, 5][6, 7, 8]]
        return ((-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1))
    def in_board(self, x, y, a, i=1):
        if (x + a[0]*i) < 0: return False
        if (Board.TileNum- 1) < (x + a[0]*i): return False
        if (y + a[1]*i) < 0: return False
        if (Board.TileNum - 1) < (y + a[1]*i): return False
        return True
    def is_enemy_stone(self, stone):
        if   stone == 0: return False
        elif stone == self.__stone: return False
        else: return True
    def exist_my_stone(self, stones, x, y, a): # 2つ以上先に自石があるか（敵石をはさんだ位置に自石があるか）
        for i in range(2, Board.TileNum):
            if self.in_board(x, y, a, i):
                if   self.__stone == stones[y+(a[1]*i)][x+(a[0]*i)]: return True
                elif 0            == stones[y+(a[1]*i)][x+(a[0]*i)]: return False
        return False
    def draw(self):
        for c in self.Candidates:
            pyxel.circ(c[0] * Board.TileSize + Board.TileSize//2, c[1] * Board.TileSize + Board.TileSize//2, Board.TileSize//2, self.__get_color(c))

    def __get_color(self, c):
        if StoneType.White == self.__stone:
            if self.is_enter_mouse(c): return 10
            else: return 7 if self.__flash_wait // 2 - 1 < pyxel.frame_count % self.__flash_wait else Board.Color
        else:
            if self.is_enter_mouse(c): return 5
            else: return 0 if self.__flash_wait // 2 - 1 < pyxel.frame_count % self.__flash_wait else Board.Color

    def is_enter_mouse(self, c):
        return (c[0] == self.__mouse_pos[0] and c[1] == self.__mouse_pos[1])
 
    def update(self):
        self.__mouse_pos[0] = pyxel.mouse_x // Board.TileSize
        self.__mouse_pos[1] = pyxel.mouse_y // Board.TileSize
        if pyxel.btnr(pyxel.MOUSE_LEFT_BUTTON):
            for c in self.Candidates:
                if c[0] == self.__mouse_pos[0] and \
                   c[1] == self.__mouse_pos[1]:
                    return True
        return False

    def get_reverse_stones(self, stones, x, y):
        self.__reverses.clear()
        for a in self.get_adjacents(): # 隣接マス
            if self.in_board(x, y, a): # 隣接マスのうちボード内にあるマス
                if self.is_enemy_stone(stones[(y+a[1])][(x+a[0])]): # 隣が敵石である
                    if self.exist_my_stone(stones, x, y, a): # 敵石をはさんだ位置に自石がある
                        # 設置した自石との間にある敵石をリバース対象としてリストアップする
                        self.__reverses.extend(self.__get_reverse_stones(stones, x, y, a))
                        print(self.__get_reverse_stones(stones, x, y, a))
        print('reverse', self.__reverses)
    def __get_reverse_stones(self, stones, x, y, a):
        targets = []
        for i in range(1, Board.TileNum): # 2つ以上先に自石があるか（敵石をはさんだ位置に自石があるか）
            targets.append((x+(a[0]*i), y+(a[1]*i)))
            if   self.__stone == stones[y+(a[1]*i)][x+(a[0]*i)]:
                targets.pop()
                return targets
            elif 0            == stones[y+(a[1]*i)][x+(a[0]*i)]: return []
        return []

    def is_gameover(self, stones):
        # すべてのマスが石で埋まった
        if numpy.count_nonzero(stones) == (Board.TileNum ** 2):
            print('すべてのマスが石で埋まった')
            return True
        # 両者ともに挟める石がない
        if 2 <= self.__pass_count:
            print('両者ともに挟める石がない')
            return True
        return False

App()
