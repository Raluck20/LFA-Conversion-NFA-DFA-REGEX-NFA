from .DFA import DFA

from dataclasses import dataclass
from collections.abc import Callable

EPSILON = ''  # this is how epsilon is represented by the checker in the transition function of NFAs


@dataclass
class NFA[STATE]:
    S: set[str]
    K: set[STATE]
    q0: STATE
    d: dict[tuple[STATE, str], set[STATE]]
    F: set[STATE]

    def epsilon_closure(self, state: STATE) -> set[STATE]:
        # compute the epsilon closure of a state (you will need this for subset construction)
        # see the EPSILON definition at the top of this file
        closure = set()
        stack = [state]

        while stack:
            current_state = stack.pop()
            closure.add(current_state)

            if (current_state, EPSILON) in self.d:
                stack.extend(self.d[(current_state, EPSILON)] - closure)

        return closure

    def subset_construction(self) -> DFA[frozenset[STATE]]:
        # convert this nfa to a dfa using the subset construction algorithm
        epsilon_closure_q0 = frozenset(self.epsilon_closure(self.q0))
        dfa_states = {epsilon_closure_q0}
        dfa_transitions = {}
        stack = [epsilon_closure_q0]

        while stack:
            current_subset = stack.pop()

            for letter in self.S:
                # obtin urmatoarele stari posibile dupa aplicarea simbolului curent asupra fiecarei stari din subsetul curent
                next_states = set(state for st in current_subset for state in self.d.get((st, letter), set()))
                # calculez inchiderea epsilon a starilor urmatoare
                epsilon_closure_next = frozenset(state for st in next_states for state in self.epsilon_closure(st))
                
                # verific daca starea obtinuta nu este deja in setul de stari ale dfa ului
                if epsilon_closure_next not in dfa_states:
                    dfa_states.add(epsilon_closure_next)
                    stack.append(epsilon_closure_next)

                dfa_transitions[(current_subset, letter)] = epsilon_closure_next

        dfa_final_states = {state for state in dfa_states if state & self.F}

        return DFA(S=self.S,
                   K=dfa_states,
                   q0=epsilon_closure_q0,
                   d=dfa_transitions,
                   F=dfa_final_states)



    def remap_states[OTHER_STATE](self, f: 'Callable[[STATE], OTHER_STATE]') -> 'NFA[OTHER_STATE]':
        # optional, but may be useful for the second stage of the project. Works similarly to 'remap_states'
        # from the DFA class. See the comments there for more details.
        pass