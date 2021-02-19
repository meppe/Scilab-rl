from stable_baselines3.common.callbacks import EvalCallback, BaseCallback
from typing import Any, Callable, Dict, List, Optional, Union
from stable_baselines3.common.vec_env import DummyVecEnv, VecEnv, sync_envs_normalization
import gym
import numpy as np
import os
import warnings
from util.custom_evaluation import evaluate_policy
from stable_baselines3.common.base_class import BaseAlgorithm
from stable_baselines3.common.off_policy_algorithm import OffPolicyAlgorithm
from stable_baselines3.common import logger
from collections import deque
import time
from stable_baselines3.common.utils import safe_mean

class CustomEvalCallback(EvalCallback):
    """
    Callback for evaluating an agent.

    :param eval_env: The environment used for initialization
    :param callback_on_new_best: Callback to trigger
        when there is a new best model according to the ``mean_reward``
    :param n_eval_episodes: The number of episodes to test the agent
    :param eval_freq: Evaluate the agent every eval_freq call of the callback.
    :param log_path: Path to a folder where the evaluations (``evaluations.npz``)
        will be saved. It will be updated at each evaluation.
    :param deterministic: Whether the evaluation should
        use a stochastic or deterministic actions.
    :param deterministic: Whether to render or not the environment during evaluation
    :param render: Whether to render or not the environment during evaluation
    :param verbose:
    """

    def __init__(
        self,
        eval_env: Union[gym.Env, VecEnv],
        n_eval_episodes: int = 5,
        eval_freq: int = 10000,
        log_path: str = None,
        deterministic: bool = True,
        render: bool = False,
        verbose: int = 1,
        early_stop_data_column: str = 'test/success_rate',
        early_stop_threshold: float = 1.0,
        early_stop_last_n: int = 5,
        model: OffPolicyAlgorithm = None
    ):
        super(EvalCallback, self).__init__(verbose=verbose)
        self.n_eval_episodes = n_eval_episodes
        self.eval_freq = eval_freq
        self.best_mean_reward = -np.inf
        self.best_mean_success = -np.inf
        self.deterministic = deterministic
        self.render = render
        eval_history_column_names = ['test/mean_reward', 'test/success_rate']
        self.eval_histories = {}
        for name in eval_history_column_names:
            self.eval_histories[name] = []
        self.early_stop_data_column = early_stop_data_column
        self.early_stop_threshold = early_stop_threshold
        self.early_stop_last_n = early_stop_last_n
        self.model = model

        eval_env = BaseAlgorithm._wrap_env(eval_env)
        # Convert to VecEnv for consistency
        if not isinstance(eval_env, VecEnv):
            eval_env = DummyVecEnv([lambda: eval_env])

        if isinstance(eval_env, VecEnv):
            assert eval_env.num_envs == 1, "You must pass only one environment for evaluation"

        self.eval_env = eval_env
        self.log_path = log_path
        self.best_model_save_path = None
        self.evaluations_results = []
        self.evaluations_timesteps = []
        self.evaluations_length = []

    def _on_step(self) -> bool:
        if self.eval_freq > 0 and self.n_calls % self.eval_freq == 0:
            # Sync training and eval env if there is VecNormalize
            sync_envs_normalization(self.training_env, self.eval_env)

            episode_rewards, episode_lengths, episode_successes = evaluate_policy(
                self.model,
                self.eval_env,
                n_eval_episodes=self.n_eval_episodes,
                render=self.render,
                deterministic=self.deterministic,
                return_episode_rewards=True,
            )

            mean_reward, std_reward = np.mean(episode_rewards), np.std(episode_rewards)
            mean_ep_length, std_ep_length = np.mean(episode_lengths), np.std(episode_lengths)
            mean_success, std_success = np.mean(episode_successes), np.std(episode_successes)

            if self.verbose > 0:
                print(f"Eval num_timesteps={self.num_timesteps}, " f"episode_reward={mean_reward:.2f} +/- {std_reward:.2f}")
                print(f"Episode length: {mean_ep_length:.2f} +/- {std_ep_length:.2f}")
            logger.record("test/mean_reward", float(mean_reward))
            logger.record("test/std_reward", float(std_reward))
            logger.record("test/mean_ep_length", mean_ep_length)
            logger.record("test/success_rate", mean_success)

            self.eval_histories['test/success_rate'].append(mean_success)
            self.eval_histories['test/mean_reward'].append(mean_reward)

            # if mean_reward > self.best_mean_reward:
            #     if self.verbose > 0:
            #         print("New best mean reward!")
            #     if self.best_model_save_path is not None:
            #         self.model.save(os.path.join(self.best_model_save_path, "best_model"))
            #     self.best_mean_reward = mean_reward
            #     # Trigger callback if needed
            #     if self.callback is not None:
            #         return self._on_event()
            if mean_success > self.best_mean_success:
                if self.verbose > 0:
                    print("New best mean success rate!")
                if self.log_path is not None:
                    self.model.save(os.path.join(self.log_path, "best_model"))
                self.best_mean_success = mean_success
            if self.model is not None:
                self.dump_model_logs()
            if len(self.eval_histories[self.early_stop_data_column]) >= self.early_stop_last_n:
                mean_val = np.mean(self.eval_histories[self.early_stop_data_column][-self.early_stop_last_n:])
                if  mean_val >= self.early_stop_threshold:
                    logger.info("Early stop threshold for {} met: Average over last {} evaluations is {} and threshold is {}. Stopping training.".format(self.early_stop_data_column, self.early_stop_last_n, mean_val, self.early_stop_threshold))
                    if self.log_path is not None:
                        self.model.save(os.path.join(self.log_path, "early_stop_model"))
                    return False
        return True

    def dump_model_logs(self):
        """
        Write log.
        """
        fps = int(self.model.num_timesteps / (time.time() - self.model.start_time))
        logger.record("time/episodes", self.model._episode_num, exclude="tensorboard")
        if len(self.model.ep_info_buffer) > 0 and len(self.model.ep_info_buffer[0]) > 0:
            logger.record("rollout/ep_rew_mean", safe_mean([ep_info["r"] for ep_info in self.model.ep_info_buffer]))
            logger.record("rollout/ep_len_mean", safe_mean([ep_info["l"] for ep_info in self.model.ep_info_buffer]))
        logger.record("time/fps", fps)
        logger.record("time/time_elapsed", int(time.time() - self.model.start_time), exclude="tensorboard")
        logger.record("time/total timesteps", self.model.num_timesteps, exclude="tensorboard")
        if self.model.use_sde:
            logger.record("train/std", (self.model.actor.get_std()).mean().item())

        if len(self.model.ep_success_buffer) > 0:
            logger.record("rollout/success rate", safe_mean(self.model.ep_success_buffer))
        # Pass the number of timesteps for tensorboard
        logger.dump(step=self.model.num_timesteps)
