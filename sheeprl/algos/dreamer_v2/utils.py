from typing import TYPE_CHECKING, List, Optional, Union

import gymnasium as gym
import numpy as np
import torch
import torch.nn as nn
from lightning import Fabric
from torch import Tensor, nn
from torch.distributions import Independent, OneHotCategoricalStraightThrough

from sheeprl.utils.env import make_dict_env

if TYPE_CHECKING:
    from sheeprl.algos.dreamer_v2.agent import Player

from sheeprl.algos.dreamer_v1.args import DreamerV1Args
from sheeprl.algos.dreamer_v2.args import DreamerV2Args


def compute_stochastic_state(
    logits: Tensor,
    discrete: int = 32,
) -> Tensor:
    """
    Compute the stochastic state from the logits computed by the transition or representaiton model.

    Args:
        logits (Tensor): logits from either the representation model or the transition model.
        discrete (int, optional): the size of the Categorical variables.
            Defaults to 32.

    Returns:
        The sampled stochastic state.
    """
    logits = logits.view(*logits.shape[:-1], -1, discrete)
    dist = Independent(OneHotCategoricalStraightThrough(logits=logits), 1)
    return dist.rsample()


def init_weights(m: nn.Module):
    """
    Initialize the parameters of the m module acording to the Xavier
    normal method.

    Args:
        m (nn.Module): the module to be initialized.
    """
    if isinstance(m, (nn.Conv2d, nn.ConvTranspose2d)):
        nn.init.xavier_normal_(m.weight.data)
        if m.bias is not None:
            nn.init.constant_(m.bias.data, 0)
    elif isinstance(m, nn.Linear):
        nn.init.xavier_normal_(m.weight.data)
        nn.init.constant_(m.bias.data, 0)


def compute_lambda_values(
    rewards: Tensor,
    values: Tensor,
    continues: Tensor,
    bootstrap: Optional[Tensor] = None,
    horizon: int = 15,
    lmbda: float = 0.95,
) -> Tensor:
    if bootstrap is None:
        bootstrap = torch.zeros_like(values[-1:])
    agg = bootstrap
    next_val = torch.cat((values[1:], bootstrap), dim=0)
    inputs = rewards + continues * next_val * (1 - lmbda)
    lv = []
    for i in reversed(range(horizon)):
        agg = inputs[i] + continues[i] * lmbda * agg
        lv.append(agg)
    return torch.cat(list(reversed(lv)), dim=0)


@torch.no_grad()
def test(
    player: "Player",
    fabric: Fabric,
    args: Union[DreamerV2Args, "DreamerV1Args"],
    cnn_keys: List[str],
    mlp_keys: List[str],
    test_name: str = "",
):
    """Test the model on the environment with the frozen model.

    Args:
        player (Player): the agent which contains all the models needed to play.
        fabric (Fabric): the fabric instance.
        args (Union[DreamerV2Args, DreamerV1Args]): the hyper-parameters.
        cnn_keys (Sequence[str]): the keys encoded by the cnn encoder.
        mlp_keys (Sequence[str]): the keys encoded by the mlp encoder.
        test_name (str): the name of the test.
            Default to "".
    """
    env: gym.Env = make_dict_env(
        args.env_id, args.seed, 0, args, fabric.logger.log_dir, "test" + (f"_{test_name}" if test_name != "" else "")
    )()
    done = False
    cumulative_rew = 0
    device = fabric.device
    next_obs = env.reset(seed=args.seed)[0]
    for k in next_obs.keys():
        next_obs[k] = torch.from_numpy(next_obs[k]).view(1, *next_obs[k].shape).float()
    player.num_envs = 1
    player.init_states()
    while not done:
        # Act greedly through the environment
        preprocessed_obs = {}
        for k, v in next_obs.items():
            if k in cnn_keys:
                preprocessed_obs[k] = v[None, ...].to(device) / 255 - 0.5
            elif k in mlp_keys:
                preprocessed_obs[k] = v[None, ...].to(device)
        real_actions = player.get_greedy_action(
            preprocessed_obs, False, {k: v for k, v in preprocessed_obs.items() if k.startswith("mask")}
        )
        if player.actor.is_continuous:
            real_actions = torch.cat(real_actions, -1).cpu().numpy()
        else:
            real_actions = np.array([real_act.cpu().argmax(dim=-1).numpy() for real_act in real_actions])

        # Single environment step
        next_obs, reward, done, truncated, _ = env.step(real_actions.reshape(env.action_space.shape))
        for k in next_obs.keys():
            next_obs[k] = torch.from_numpy(next_obs[k]).view(1, *next_obs[k].shape).float()
        done = done or truncated or args.dry_run
        cumulative_rew += reward
    fabric.print("Test - Reward:", cumulative_rew)
    fabric.logger.log_metrics({"Test/cumulative_reward": cumulative_rew}, 0)
    env.close()