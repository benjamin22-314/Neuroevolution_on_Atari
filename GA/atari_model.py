# In the GA folder
# 

import cv2
import numpy as np

import torch
import torch.nn as nn
from torch.autograd import Variable
import torch.nn.functional as F

import gym
from gym import wrappers
import random

import base_model


class AtariModel():
    """
    Takes config which has atari game parameters.
    Also takes seed_dict which is passed to BigModel.
    """
    def __init__(self, seed_dict, config):
        self.get_seed = config['get_seed']
        self.env_name = config['env']
        self.max_frames_per_episode = config['max_frames_per_episode']
        self.output_fname = config['output_fname']
        self.model = base_model.BigModel(seed_dict, config)

    def convert_state(self, state):
        return cv2.resize(cv2.cvtColor(state, cv2.COLOR_RGB2GRAY), (64, 64)) / 255.0

    def reset(self, env):
        return self.convert_state(env.reset())

    def evaluate_model(self, monitor=False, max_noop=30):
        """
        outputs reward and frames. Can create an mp3 with monitor=True
        """
        env = gym.make(self.env_name)
        env.seed(0)

        cur_states = [self.reset(env)] * 4
        total_reward = 0
        total_frames = 0
        old_lives = env.env.ale.lives()

        if monitor:
            env = wrappers.Monitor(env, self.output_fname)

        env.reset()

        # implement random no-operations
        random.seed(next(self.get_seed))
        noops = random.randint(0, max_noop)
        for _ in range(noops):
            observation, reward, done, _ = env.step(0)
            total_reward += reward
            if done:
                break
            cur_states.pop(0)
            new_frame = self.convert_state(observation)
            cur_states.append(new_frame)

        for t in range(self.max_frames_per_episode):

            total_frames += 4

            #  model output
            values = self.model(Variable(torch.Tensor([cur_states])))[0]
            action = np.argmax(values.data.numpy()[:env.action_space.n])
            observation, reward, done, _ = env.step(action)

            # update current state
            total_reward += reward

            if monitor:
                new_lives = env.env.env.ale.lives()
                if old_lives < new_lives:
                    break
            else:
                new_lives = env.env.ale.lives()
                if old_lives < new_lives:
                    break
            old_lives = new_lives

            # break if it's been one life and 0 reward
            # need to be careful with this, it won't generalise to other games
            if old_lives == 3:
                if total_reward == 0:
                    break

            if done:
                break
            cur_states.pop(0)
            new_frame = self.convert_state(observation)
            cur_states.append(new_frame)

        env.env.close()
        return total_reward, total_frames
