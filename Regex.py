from .NFA import NFA
from dataclasses import dataclass
from typing import List
import copy
EPSILON = ''

class Regex:
    def thompson(self) -> NFA[int]:
        raise NotImplementedError('the thompson method of the Regex class should never be called')



@dataclass
class Character(Regex):
    symbol: str

    def thompson(self) -> NFA[int]:
        return NFA(S={self.symbol}, K={0, 1}, q0=0, d={(0, self.symbol): {1}}, F={1})

@dataclass
class Concat(Regex):
    def __init__(self, regex1: Regex, regex2: Regex):
        self.regex1 = regex1
        self.regex2 = regex2

    def thompson(self) -> NFA[int]:
        nfa1 = self.regex1.thompson()
        nfa2 = self.regex2.thompson()

        # Calculez offset-ul pentru starile celui de-al doilea NFA
        offset = max(nfa1.K) + 1

        # Actualizez starile celui de-al doilea NFA cu offset-ul
        nfa2.K = {state + offset for state in nfa2.K}
        nfa2.F = {state + offset for state in nfa2.F}
        nfa2.q0 += offset
        nfa2.d = {(state[0] + offset, state[1]): {x + offset for x in symbols} for state, symbols in nfa2.d.items()}

        # Unific starile și tranzitiile celor doua NFA-uri
        nfa_states = nfa1.K.union(nfa2.K)
        nfa_transitions = {**nfa1.d, **nfa2.d}

        # Adaug tranzitia epsilon de la starea finala a primului NFA la starea initiala a celui de-al doilea NFA
        if nfa1.q0 in nfa1.F:
            if nfa1.q0 == nfa2.q0:
                if (max(nfa1.F), EPSILON) not in nfa_transitions:
                    nfa_transitions[(max(nfa1.F), EPSILON)] = set()
                nfa_transitions[(max(nfa1.F), EPSILON)].add(nfa2.q0)
            else:
                nfa_transitions.setdefault((max(nfa1.F), EPSILON), set()).add(nfa2.q0)

        # Adaug tranzitia epsilon de la starea finala a primului NFA la starea inițiala a celui de-al doilea NFA
        nfa_transitions.setdefault((max(nfa1.K), EPSILON), set()).add(nfa2.q0)

        # Actualizez starile finale ale primului NFA cu offset-ul
        nfa1.F = {state + offset for state in nfa1.F}

        # Actualizez starile finale ale celui de-al doilea NFA
        nfa_final_states = nfa2.F

        # Elimin starea finala a primului NFA din starile finale ale intregului NFA
        nfa_final_states.discard(max(nfa1.K))

        # Adaug starea finala a celui de-al doilea NFA la starile finale ale intregului NFA
        nfa_final_states.add(max(nfa2.K))

        return NFA(S=nfa1.S.union(nfa2.S),
                   K=nfa_states,
                   q0=nfa1.q0,
                   d=nfa_transitions,
                   F=nfa_final_states)


@dataclass
class MyUnion(Regex):
    def __init__(self, regex1: 'Regex', regex2: 'Regex') -> None:
        self.regex1 = copy.deepcopy(regex1)
        self.regex2 = copy.deepcopy(regex2)

    def thompson(self) -> NFA[int]:
        nfa1 = self.regex1.thompson()
        nfa2 = self.regex2.thompson()

        offset1 = 1
        offset2 = 1 + len(nfa1.K)

        # Remapeaz starile pentru nfa1 și nfa2
        remapped_states_nfa1 = {state: state + offset1 for state in nfa1.K}
        remapped_states_nfa2 = {state: state + offset2 for state in nfa2.K}

        # Construiesc noul NFA
        S = nfa1.S.union(nfa2.S)
        K = set(remapped_states_nfa1.values()).union(remapped_states_nfa2.values()).union({0, offset2 + len(nfa2.K)})
        q0= 0

        # Construiesc tranzitiile pentru noul NFA
        d = {}
        for (state, symbol), next_states in nfa1.d.items():
            d[(remapped_states_nfa1[state], symbol)] = {remapped_states_nfa1[s] for s in next_states}
        for (state, symbol), next_states in nfa2.d.items():
            d[(remapped_states_nfa2[state], symbol)] = {remapped_states_nfa2[s] for s in next_states}

        d[(q0, EPSILON)] = {remapped_states_nfa1[nfa1.q0], remapped_states_nfa2[nfa2.q0]}
        F = {offset2 + len(nfa2.K)}

        for f in nfa1.F:
            d.setdefault((remapped_states_nfa1[f], EPSILON), set()).add(offset2 + len(nfa2.K))
        for f in nfa2.F:
            d.setdefault((remapped_states_nfa2[f], EPSILON), set()).add(offset2 + len(nfa2.K))

        return NFA(S, K, q0, d, F)

@dataclass
class Star(Regex):
    regex: Regex

    def thompson(self) -> NFA[int]:
        nfa = self.regex.thompson()

        # Starile noi pentru constructia operatiei Star
        s0, s1 = max(nfa.K) + 1, max(nfa.K) + 2

        # Tranzitiile noi pentru constructia operatiei Star
        transitions = {
            (s0, EPSILON): {nfa.q0, s1},
            (max(nfa.F), EPSILON): {nfa.q0, s1},
            (s1, EPSILON): {s0},
        }

        # Actualizez starile, alfabetul si tranzitiile pentru noul NFA
        K_star = nfa.K.union({s0, s1})
        d_star = {**nfa.d, **transitions}
        F_star = {s1}

        return NFA(S=nfa.S, K=K_star, q0=s0, d=d_star, F=F_star)

@dataclass
class Question(Regex):
    def __init__(self, regex: 'Regex') -> None:
        self.regex = regex

    def thompson(self) -> NFA[int]:
        # Construiesc NFA pentru regex
        nfa_regex = self.regex.thompson()

        # Aloc noi stari pentru NFA-ul rezultat
        start_state = 0
        end_state = max(nfa_regex.K) + 1

        # Initializeaza seturile și dictionarul pentru noul NFA
        S = nfa_regex.S.union({EPSILON})
        K = nfa_regex.K.union({start_state, end_state})
        d = {(start_state, EPSILON): {nfa_regex.q0, end_state}}
        F = {end_state}

        # Adaug tranzițiile din NFA-ul original
        for (state, symbol), next_states in nfa_regex.d.items():
            d[(state, symbol)] = next_states

        # Adaug starile finale ale NFA-ului original la starea finala a noului NFA
        for f_state in nfa_regex.F:
            d.setdefault((f_state, EPSILON), set()).add(end_state)

        return NFA(S, K, start_state, d, F)

@dataclass
class Plus(Regex):
    def __init__(self, regex: 'Regex') -> None:
        # Construirea operatiei Plus ca fiind concatenarea dintre regex si Star(regex)
        self.regex = Concat(regex, Star(regex))

    def thompson(self) -> NFA[int]:
        return self.regex.thompson()
@dataclass
class LowerCase(Regex):
    def __init__(self) -> None:
        # Construirea operatiei LowerCase ca fiind reuniunea tuturor literelor mici
        regex = Character('a')
        for char in range(ord('b'), ord('z') + 1):
            regex = MyUnion(regex, Character(chr(char)))
        self.regex = regex

    def thompson(self) -> NFA[int]:
        return self.regex.thompson()

@dataclass
class UpperCase(Regex):
    def __init__(self) -> None:
        # Construirea operatiei UpperCase ca fiind reuniunea tuturor literelor mari
        regex = Character('A')
        for char in range(ord('B'), ord('Z') + 1):
            regex = MyUnion(regex, Character(chr(char)))
        self.regex = regex

    def thompson(self) -> NFA[int]:
        return self.regex.thompson()

@dataclass
class Digits(Regex):
    def __init__(self) -> None:
        # Construirea operatiei Digits ca fiind reuniunea tuturor cifrelor
        regex = Character('0')
        for char in range(ord('1'), ord('9') + 1):
            regex = MyUnion(regex, Character(chr(char)))
        self.regex = regex

    def thompson(self) -> NFA[int]:
        return self.regex.thompson()

def parse_regex(regex: str) -> Regex:
    # Stive pentru operatori si operanzi
    OPs: List[str] = []
    stack: List[Regex] = []
    # Variabila pentru a verifica daca expresia regulata este corecta
    ok: bool = False
    # Setul de simboluri
    symbol = set(['*', '?', '+', '|', '(', ')', '[', ']'])
    # Pozitia curenta in expresia regulata
    i = 0

    def handle_symbol():
        nonlocal i, ok
        if regex[i] == '(':
            handle_opening_parenthesis()
        elif regex[i] == ')':
            handle_closing_parenthesis()
        elif regex[i] in ['?', '*', '+']:
            handle_QSP()
        elif regex[i] == '|':
            handle_pipe()
        elif regex[i] == '[':
            handle_square_bracket()

    def handle_opening_parenthesis():
        nonlocal i, ok
        if ok:
            OPs.append('.')
        OPs.append('(')
        ok = False
        i += 1

    def handle_closing_parenthesis():
        nonlocal i, ok
        while OPs[-1] != '(':
            operator = OPs.pop()
            op2 = stack.pop()
            op1 = stack.pop()
            if operator == '|':
                stack.append(MyUnion(op1, op2))
            else:
                stack.append(Concat(op1, op2))
        OPs.pop()
        ok = True
        i += 1

    def handle_QSP():
        nonlocal i, ok
        op1 = stack.pop()
        if regex[i] == '*':
            stack.append(Star(op1))
        elif regex[i] == '?':
            stack.append(Question(op1))
        else:
            stack.append(Plus(op1))
        ok = True
        i += 1

    def handle_pipe():
        nonlocal i, ok
        while OPs and OPs[-1] == '.':
            OPs.pop()
            op2 = stack.pop()
            op1 = stack.pop()
            stack.append(Concat(op1, op2))
        OPs.append('|')
        ok = False
        i += 1

    def handle_square_bracket():
        nonlocal i, ok
        if ok:
            OPs.append('.')
        end_pos = regex.find(']', i)
        if end_pos != -1 and end_pos > i + 2:
            str = regex[i + 1:end_pos]
            handle_string(str)
            i = end_pos + 1
            ok = True
        else:
            raise ValueError("Error in square brackets")

    def handle_string(str: str):
        nonlocal i
        if str == 'a-z':
            stack.append(LowerCase())
        elif str == 'A-Z':
            stack.append(UpperCase())
        elif str == '0-9':
            stack.append(Digits())
        else:
            raise ValueError("Error in square brackets")

    # Parcurg expresia regulata
    while i < len(regex):
        if regex[i] == ' ':
            i += 1
        elif regex[i] not in symbol:
            if ok:
                OPs.append('.')
            ok = True

            if regex[i] == '\\' and regex[i + 1] in ['*', '?', '+', '|', '(', ')', '[', ']', ' ', '/', '\\']:
                stack.append(Character(regex[i + 1]))
                i += 1
            else:
                stack.append(Character(regex[i]))

            i += 1
        else:
            handle_symbol()

    # Construiesc expresia regulata finala
    while OPs:
        op2 = stack.pop()
        op1 = stack.pop()

        if OPs.pop() == '|':
            stack.append(MyUnion(op1, op2))
        else:
            stack.append(Concat(op1, op2))

    # Returnez expresia regulata rezuultata
    return stack[0]