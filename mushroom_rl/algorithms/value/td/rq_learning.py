import numpy as np

from mushroom_rl.algorithms.value.td import TD
from mushroom_rl.utils.table import Table


class RQLearning(TD):
    """
    RQ-Learning algorithm.
    "Exploiting Structure and Uncertainty of Bellman Updates in Markov Decision
    Processes". Tateo D. et al.. 2017.

    """
    def __init__(self, mdp_info, policy, learning_rate, off_policy=False,
                 beta=None, delta=None):
        """
        Constructor.

        Args:
            off_policy (bool, False): whether to use the off policy setting or
                the online one;
            beta (Parameter, None): beta coefficient;
            delta (Parameter, None): delta coefficient.

        """
        self.off_policy = off_policy
        if delta is not None and beta is None:
            self.delta = delta
            self.beta = None
        elif delta is None and beta is not None:
            self.delta = None
            self.beta = beta
        else:
            raise ValueError('delta or beta parameters needed.')

        self.Q = Table(mdp_info.size)
        self.Q_tilde = Table(mdp_info.size)
        self.R_tilde = Table(mdp_info.size)

        self._add_save_attr(
            off_policy='pickle',
            delta='pickle',
            beta='pickle',
            Q='pickle',
            Q_tilde='pickle',
            R_tilde='pickle'
        )

        super().__init__(mdp_info, policy, self.Q, learning_rate)

    def _update(self, state, action, reward, next_state, absorbing):
        alpha = self.alpha(state, action, target=reward)
        self.R_tilde[state, action] += alpha * (reward - self.R_tilde[
            state, action])

        if not absorbing:
            q_next = self._next_q(next_state)

            if self.delta is not None:
                beta = alpha * self.delta(state, action, target=q_next,
                                          factor=alpha)
            else:
                beta = self.beta(state, action, target=q_next)

            self.Q_tilde[state, action] += beta * (q_next - self.Q_tilde[
                state, action])

        self.Q[state, action] = self.R_tilde[
            state, action] + self.mdp_info.gamma * self.Q_tilde[state, action]

    def _next_q(self, next_state):
        """
        Args:
            next_state (np.ndarray): the state where next action has to be
                evaluated.

        Returns:
            The weighted estimator value in 'next_state'.

        """
        if self.off_policy:
            return np.max(self.Q[next_state, :])
        else:
            self.next_action = self.draw_action(next_state)

            return self.Q[next_state, self.next_action]