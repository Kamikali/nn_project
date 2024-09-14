import numpy as np
from enum import Enum


class PlayerNr(Enum):
    """
    Define an enumeration for player numbers bound to more reasonable names.
    """

    X = 1
    O = -1


class Player():
    """
    Represents a player in the game. 
    There are always exactly two players, Player X and 0 required for a game to launch.

    Attributes:

        fields_taken:
            Fields in the TikTakToe matrix picked by the corresponding player.

        player_nr:
            An identifier whether a player is playing as X or O.

    Methods:
        take_field:
        Takes a given field in the game matrix if it is free.
    """

    def __init__(self) -> None:
        self.fields_taken = list()
        self.player_nr = None

    def take_field(self, game, field) -> bool:
        """
        Makes a move in a given game

        Parameters:
            game:
                A game object of TikTakToe

            field:
                The field a player is trying to occupy with his move.
        """
        if field not in range(0, 9):
            raise Exception("Only fields 0 to 8 exist.")
        game.occupy_field(self, self.player_nr, field)

class InputPlayer(Player):

    """
    A player that asks for user input every turn.
    """

    def take_field(self, game) -> bool:
        """
        Makes a random legal move in a given game

        Parameters:
            game:
                A game object of TikTakToe
        """

        field = int(input("Take a field, 0 - 8: "))

        while field not in range(0, 9):
            field = int(input("Wrong input. Take a field, 0 - 8: "))
        game.occupy_field(self, self.player_nr, field)


class RandomPlayer(Player):

    """
    A player which will always take a random free field on the game matrix.
    """

    def take_field(self, game) -> bool:
        """
        Makes a random legal move in a given game

        Parameters:
            game:
                A game object of TikTakToe
        """

        import random
        field = random.randint(0, 8)

        taken_fields = []
        for field in game.player_x.fields_taken:
            taken_fields.append(field)
        for field in game.player_o.fields_taken:
            taken_fields.append(field)

        while field in taken_fields:
            field = random.randint(0, 8)

        if field not in range(0, 9):
            raise Exception("Only fields 0 to 8 exist.")
        game.occupy_field(self, self.player_nr, field)


class TikTakToe():

    """
    Class that hosts a TikTakToe game.
    Each instantiation of the class is a playble game of player O against player X.

    We encode our 3x3 TikTakToe game matrix as following:
    Empty fields = 0
    Fields chosen by player X = 1
    Fields chosen by player O = 2

    Parameters:
        player_x: a reference to the first player
        player_o: a ference to the second player
        player_turn: Of type PlayerNr. Holds which player can make the next move.
        is_ongoing: boolean whether a game is finished or not


    Methods:
        check_for_win: 
        checks whether a player has won

        print: 
        prettyprints the game matrix

        occupy_field:
        Is called when a player is trying to make a move to take a field in the game matrix.

        reset:
        resets a game into beginning state
    """

    def __init__(self, starting_player_x: Player, second_player_o: Player):
        """
        Creates a game.

        Parameters:
            starting_player_x:
            The first player, using X in the game matrix, represented by a 0.

            second_player_o:
            The second player, using O in the game matrix, represented by a 1.

            player_turn: 
            Stores whose players turn it currently is. Starting with player X.

            #game_matrix:
            #A 3x3 matrix that is used to print the game state for humans.

            is_onging:
            True as long as there is no winner yet or not all nine 
            fields are in the game matrix taken.

            result:
            A string to store a game's end result.
            Possible values are "x_win", "o_win", "draw" and "error".

        """

        if len(starting_player_x.fields_taken) > 0 or len(second_player_o.fields_taken) > 0:
            raise Exception('A given player already has taken fields. Use player.clean_fields.')


        self.player_x = starting_player_x
        self.player_x.player_nr = PlayerNr.X

        self.player_o = second_player_o
        self.player_o.player_nr = PlayerNr.O

        self.player_turn = PlayerNr.X   # player X starts the game

        self.is_ongoing = True
        self.result = None # will be set after game has ended

    def reset(self):
        self.player_x.fields_taken = list()
        self.player_o.fields_taken = list()
        self.player_turn = PlayerNr.X
        self.is_ongoing = True

    def get_game_matrix(self) -> list:
        
        game_matrix = [0 for _ in range(3 * 3)] # storing game states as a list

        for field in self.player_x.fields_taken:
            game_matrix[field] = 1
        for field in self.player_o.fields_taken:
            game_matrix[field] = -1

        return game_matrix

    def print(self, raw=False):
        """
        Prettyprints the game matrix, readable for humans.

        # TODO actually pretty print it

        Paramters:
            raw:
                If set to true, print the game_matrix as its original list form.
        """
        
        game_matrix = self.get_game_matrix()

        if raw:
            print(game_matrix)
        else:
            pretty_matrix = [0 for _ in range(3 * 3)] # using the nice numpy 2d matrix feature here because it prints nicely

            for index, field in enumerate(game_matrix):
                if field == 0:
                    pretty_matrix[index] = '-'
                if field == PlayerNr.X.value:
                    pretty_matrix[index] = 'X'
                if field == PlayerNr.O.value:
                    pretty_matrix[index] = 'O'

            pretty_matrix = np.char.array(pretty_matrix)
            print(pretty_matrix.reshape((3, 3)))

    def occupy_field(self, player: Player, player_nr: PlayerNr, field) -> bool:
        
        # check if player can make a move
        if player_nr != self.player_turn:
            raise Exception(f"It is not this players turn yet. Player: {player.player_nr}")
    
        
        # check if field can be occupied by player
        if field in self.player_o.fields_taken or field in self.player_x.fields_taken:
            raise Exception(f"You are trying to take an occupied field!")
        
        # change turn
        if self.player_turn == PlayerNr.X:
            self.player_turn = PlayerNr.O
        else:
            self.player_turn = PlayerNr.X

        # add field to taken fields
        player.fields_taken.append(field)
        
        # check for win
        if self.check_for_win(player):
            print(f"Player {player.player_nr} has won the game!")

            if player.player_nr == PlayerNr.X:
                self.result = 'x_win'
            elif player.player_nr == PlayerNr.O:
                self.result = 'o_win'
            else:
                self.result = 'error'
            self.is_ongoing = False
        if self.check_for_draw():
            print("Draw! All fields are taken.")
            self.result = 'draw'
            self.is_ongoing = False

        return True

    def check_for_draw(self):
        if len(self.player_x.fields_taken) + len(self.player_o.fields_taken) >= 9:
            return True
        return False

    def check_for_win(self, player: Player) -> bool:
        """
        Has to be called to verify gamne state after every move made by each player.
        Checks, whether a player has won a game of TikTakToe.

        Attributes:
            win_states:
            valid combinations of moves placed on the game matrix that lead to victory.
        """

        win_states = [
            [0, 1, 2], # rows
            [3, 4, 5],
            [6, 7, 8],
            [0, 3, 6], # cols
            [1, 4, 7],
            [2, 5, 8],
            [0, 4, 8], # diagonals
            [2, 4, 6],
        ] 

        for win_state in win_states:       # iterate through win conditions
            if win_state[0] in player.fields_taken and win_state[1] in player.fields_taken and win_state[2] in player.fields_taken:
                return True
            
        return False
