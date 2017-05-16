# -*- coding: utf-8 -*-
import tensorflow as tf
import numpy as np
import random
import dqn
from collections import deque
from data.env import Env
import multiprocessing
import sys
if 'threading' in sys.modules:
    del sys.modules['threading']
from gevent import monkey; monkey.patch_all()
from gevent.pool import Pool

from tensorflow.python.framework.errors_impl import NotFoundError


class AIControl:
    def __init__(self, env):
        self.env = env

        self.input_size = self.env.state_n
        self.output_size = self.env.action_n

        self.dis = 0.9
        self.REPLAY_MEMORY = 9000
        self.max_episodes = 1500
        self.replay_buffer = deque()
        self.val = 0
        self.save_path = "./save/save_model"

    def replay_train(self, mainDQN, targetDQN, train_batch):
        x_stack = np.empty(0).reshape(0, self.input_size)
        y_stack = np.empty(0).reshape(0, self.output_size)
        for state, action, reward, next_state, done in train_batch:
            Q = mainDQN.predict(state)

            if done:
                Q[0, action] = reward
            else:
                Q[0, action] = reward + self.dis * np.max(targetDQN.predict(next_state))


            state = np.reshape(state, [30000])
            y_stack = np.vstack([y_stack, Q])
            x_stack = np.vstack([x_stack, state])

        return mainDQN.update(x_stack, y_stack)


    def get_copy_var_ops(self, dest_scope_name="target", src_scope_name="main"):
        op_holder = []

        src_vars = tf.get_collection(tf.GraphKeys.TRAINABLE_VARIABLES, scope=src_scope_name)
        dest_vars = tf.get_collection(tf.GraphKeys.TRAINABLE_VARIABLES, scope=dest_scope_name)

        for src_var, dest_var in zip(src_vars, dest_vars):
            op_holder.append(dest_var.assign(src_var.value()))

        return op_holder

    def save_state(self, main, target):
        main.save()
        target.save()

    def control_start(self):
        pool = Pool(6)
        with tf.Session() as sess:
            mainDQN = dqn.DQN(sess, self.input_size, self.output_size, name="main")
            targetDQN = dqn.DQN(sess, self.input_size, self.output_size, name="target")

            tf.global_variables_initializer().run()

            try:
                mainDQN.restore()
                targetDQN.restore()
            except NotFoundError:
                pass

            copy_ops = self.get_copy_var_ops(dest_scope_name=targetDQN.net_name, src_scope_name=mainDQN.net_name)
            sess.run(copy_ops)

            for episode in range(50, self.max_episodes):
                e = 1. / ((episode / 10) + 1)
                done = False
                step_count = 0
                state = self.env.reset()
                max_x = 0

                while not done:
                    if np.random.rand(1) < e:
                        action = self.env.get_random_actions()
                    else:
                        action = mainDQN.predict(state)
                        print("action", action)

                    next_state, reward, done, max_x = self.env.step(action)


                    if done:
                        reward = -10000

                    self.replay_buffer.append((state, action, reward, next_state, done))
                    if len(self.replay_buffer) > self.REPLAY_MEMORY:
                        self.replay_buffer.popleft()

                    state = next_state
                    step_count += 1

                    # if step_count > 10000:
                    #    break

                print("Episode: {}  steps: {}  max_x: {}".format(episode, step_count, max_x))

                if episode % 2 == 0:
                    self.save_state(mainDQN, targetDQN)

                print step_count
                print("len buffer ", len(self.replay_buffer))
                minibatch = random.sample(self.replay_buffer, int(len(self.replay_buffer) / 100))
                loss = self.replay_train(mainDQN, targetDQN, minibatch)

                print("Loss: ", loss)
                sess.run(copy_ops)

def main():
    queues = {
        'step': multiprocessing.JoinableQueue(),
        'action': multiprocessing.Queue()
    }
    tasks = multiprocessing.JoinableQueue()
    results = multiprocessing.Queue()
    env = Env()
    controller = AIControl(env)
    #pr = multiprocessing.Process(target=controller.control_start)
    #pr.start()
    controller.control_start()
    #env.start()


if __name__ == "__main__":
    main()
