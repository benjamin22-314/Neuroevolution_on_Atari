import cv2
import time
import random
import numpy as np
import matplotlib.pyplot as plt

import torch
import torch.nn as nn
from torch.autograd import Variable
import torch.nn.functional as F

import gym
from gym import wrappers

import matplotlib.pyplot as plt

import models


class RSModel():

    def __init__(self, seed, config):
        self.env_name = config['env']
        self.max_frames_per_episode = config['max_frames_per_episode']
        self.output_fname = config['output_fname']
        self.model_type = config['model']
        # below is equivalent to models.SmallModel(seed)
        self.model = getattr(models, self.model_type)(seed)

    def convert_state(self, state):
        return cv2.resize(cv2.cvtColor(state, cv2.COLOR_RGB2GRAY), (64, 64)) / 255.0

    def reset(self, env):
        return self.convert_state(env.reset())

    def evaluate_model(self, monitor=False):

        env = gym.make(self.env_name)

        cur_states = [self.reset(env)] * 4
        total_reward = 0
        total_frames = 0
        old_lives = env.env.ale.lives()

        if monitor:
            env = wrappers.Monitor(env, self.output_fname)

        env.reset()

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

            # unfortunately this isn't working.
            # if done:
            #     break
            cur_states.pop(0)
            new_frame = self.convert_state(observation)
            cur_states.append(new_frame)

        env.env.close()
        return total_reward, total_frames