import logging
from pathlib import Path
import time
import datetime
from PIL import Image

import gym
import soulsgym
from soulsgym.core.game_input import GameInput  # noqa: F401

if __name__ == "__main__":
    logging.basicConfig(filename="soulsgym.log",
                        filemode="w",
                        format="%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s",
                        datefmt='%H:%M:%S',
                        level=logging.WARNING)
    logging.getLogger().addHandler(logging.StreamHandler())
    soulsgym.set_log_level(level=logging.DEBUG)
    env = gym.make("SoulsGymIudex-v0")
    t_start = time.time()
    try:
        states = []
        i = 1
        while datetime.timedelta(seconds=time.time() - t_start).days == 0:
            print(f"Starting episode {i}")
            states = []
            state = env.reset()
            states.append(states)
            done = False
            while not done:
                next_state, reward, done, info = env.step(env.action_space.sample())
                states.append(next_state)
            seconds = round(time.time() - t_start)
            print(f"Current gym uptime: {str(datetime.timedelta(seconds=seconds))}")
            i += 1
    finally:
        # game_input = GameInput()
        # game_input._press_key(0x12)
        # game_input._press_key(0x73)
        # game_input.reset()
        t_end = time.time()
        root = Path(__file__).parent / "debug"
        root.mkdir(exist_ok=True)
        [f.unlink() for f in root.glob("*") if f.is_file()]
        for idx, img in enumerate(env.img_cache):
            im = Image.fromarray(img)
            im.save(root / ("img" + f"{idx:05d}" + ".png"))
        print(states)
        print(f"Total gym run time: {str(datetime.timedelta(seconds=round(t_end-t_start)))}")
        env.close()
