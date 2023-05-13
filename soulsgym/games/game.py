"""The ``Game`` classes provide a Python interface for the game properties of the Souls games.

They abstract the memory manipulation into properties and functions that write into the appropriate
game memory addresses.

Note:
    The interface is essentially a wrapper around the :class:`.MemoryManipulator`. As such it
    inherits the same cache restrictions. See :data:`.MemoryManipulator.cache`,
    :meth:`.Game.clear_cache` and :meth:`.MemoryManipulator.clear_cache` for more information.

Warning:
    Writing into the process memory is not guaranteed to be "stable". Race conditions with the main
    game loop *will* occur and overwrite values. Coordinates are most affected by this.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict

from soulsgym.core.game_state import GameState
from soulsgym.core.static import keybindings, keymap, actions, coordinates, player_animations
from soulsgym.core.static import critical_player_animations, boss_animations, player_stats
from soulsgym.core.static import bonfires, address_bases, address_offsets, address_base_patterns


@dataclass
class StaticGameData:
    """A container for the static game data.

    Only loads the static data required for the specific game to not clutter the game interface.
    """
    keybindings: Dict
    keymap: Dict
    actions: Dict
    coordinates: Dict
    player_animations: Dict
    critical_player_animations: Dict
    boss_animations: Dict
    player_stats: Dict
    bonfires: Dict
    address_bases: Dict
    address_offsets: Dict
    address_base_patterns: Dict

    def __init__(self, game_id: str):
        """Load the static data for the specific game.

        Args:
            game_id: The game ID.
        """
        self.keybindings = keybindings[game_id]
        self.keymap = keymap[game_id]
        self.actions = actions[game_id]
        self.coordinates = coordinates[game_id]
        self.player_animations = player_animations[game_id]
        self.critical_player_animations = critical_player_animations[game_id]
        self.boss_animations = boss_animations[game_id]
        self.player_stats = player_stats[game_id]
        self.bonfires = bonfires[game_id]
        self.address_bases = address_bases[game_id]
        self.address_offsets = address_offsets[game_id]
        self.address_base_patterns = address_base_patterns[game_id]


class Game(ABC):
    """Base class for all game interfaces.

    The game interface exposes the game properties as class properties and methods. Almost all
    properties and methods write directly into the game memory. The only exception is the
    :attr:`~.Game.camera_pose`. We haven't found a method to directly manipulate the camera pose
    and instead use a ``GameInput`` instance to manually control the camera with keystrokes.
    """

    def __init__(self):
        super().__init__()
        # Load the static data for the specific game
        self.data = StaticGameData(self.game_id)

    @property
    @abstractmethod
    def game_id(self) -> str:
        """The game ID.

        Returns:
            The game ID.
        """

    @abstractmethod
    def get_state(self) -> GameState:
        """Read the current state of the game into a :class:`.GameState`.

        Returns:
            The current game state.
        """
