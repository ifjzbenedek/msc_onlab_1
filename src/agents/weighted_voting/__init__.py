"""Weighted-voting ensembles over AgentPipelines.

Implementations of the Weighted Majority Algorithm family from
Littlestone & Warmuth (1994), adapted to the bandit setting where a
pipeline is selected per problem (running all of them is too expensive).
"""

from src.agents.weighted_voting.base import WeightedVotingBase
from src.agents.weighted_voting.wm import WeightedMajority
from src.agents.weighted_voting.wmr import RandomizedWeightedMajority
from src.agents.weighted_voting.wmr_retry import RandomizedWeightedMajorityWithRetry
from src.agents.weighted_voting.exp3 import Exp3

__all__ = [
    "WeightedVotingBase",
    "WeightedMajority",
    "RandomizedWeightedMajority",
    "RandomizedWeightedMajorityWithRetry",
    "Exp3",
]