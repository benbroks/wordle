import json
import random
  
def build_set_of_words():
    word_set = set()
    with open("5words.txt") as f:
        for line in f:
            word_set.add(line.strip())
    return word_set

def build_yes_index(word_collection):
    yes_index = [{chr(c):set() for c in range(ord('a'), ord('z')+1)} for _ in range(5)]
    for w in word_collection:
        for i in range(5):
            yes_index[i][w[i]].add(w)
    return yes_index     

def build_no_index(word_collection):
    no_index = {chr(c):set() for c in range(ord('a'), ord('z')+1)}
    for w in word_collection:
        for ord_c in range(ord('a'), ord('z')+1):
             c = chr(ord_c) 
             if c not in w:
                 no_index[c].add(w)
    return no_index

def build_not_here_index(yes_index):
    not_here_index = [{} for _ in range(5)]
    for ord_c in range(ord('a'), ord('z')+1):
        c = chr(ord_c)
        for i in range(5):
            to_add = set()
            for j in range(5):
                if i != j:
                    to_add.update(yes_index[j][c])
            to_add = to_add - yes_index[i][c]
            not_here_index[i][c] = to_add
    return not_here_index


# STRING STUFF #
def generate_all_return_strings(n):
    if n == 0:
        return [""]
    prev = generate_all_return_strings(n-1)
    return ["Y"+a for a in prev] + ["N"+a for a in prev] + ["~"+a for a in prev]

def is_valid_string(s):
    if s.count('~') == 1 and s.count('N') == 0:
        return False
    return True

# Actual Elims #
def expected_elims(w, yes_idx, no_idx, n_h_idx, total_words, pruned_strings):
    ee = 0
    for s in pruned_strings:
        ee += expected_elims_for_return_str(w, s, yes_idx, no_idx, n_h_idx, total_words)
    return ee

def expected_elims_for_return_str(w, s, yes_idx, no_idx, n_h_idx, total_words):
    words_left = set()
    for i in range(5):
        word_char = w[i]
        return_string_char = s[i]
        if return_string_char == 'Y':
            to_update = yes_idx[i][word_char]
        elif return_string_char == '~':
            to_update = n_h_idx[i][word_char]
        else:
            to_update = no_idx[word_char]
        if i == 0:
            words_left = to_update
        else:
            words_left = words_left.intersection(to_update)
    num_words_left = len(words_left)
    elims = total_words - num_words_left
    prob_elim = num_words_left / total_words
    return prob_elim * elims

def construct_cached_scores(file_to_write='cached_scores.json'):
    word_set = build_set_of_words()
    yes_index = build_yes_index(word_set)
    no_index = build_no_index(word_set)
    not_here_index = build_not_here_index(yes_index)
    
    strings_to_evaluate = generate_all_return_strings(n=5)
    pruned = [s for s in strings_to_evaluate if is_valid_string(s)]
    
    with open(file_to_write) as f:
        first_round_scores = json.load(f)
    for i,w in enumerate(word_set):
        if i % 1000 == 0:
            print("{}% complete.".format(100*i/len(word_set)))
            with open(file_to_write, 'w') as f:
                # this would place the entire output on one line
                # use json.dump(lista_items, f, indent=4) to "pretty-print" with four spaces per indent
                json.dump(first_round_scores, f)
        if w not in first_round_scores:
            first_round_scores[w] = expected_elims(
                w=w,
                yes_idx = yes_index,
                no_idx = no_index,
                n_h_idx=not_here_index,
                total_words = len(word_set),
                pruned_strings=pruned
            )
    with open(file_to_write, 'w') as f:
        # this would place the entire output on one line
        # use json.dump(lista_items, f, indent=4) to "pretty-print" with four spaces per indent
        json.dump(first_round_scores, f)
        
class Wordle:
    def __init__(self,w):
        self.w = w
    
    def guess(self,g):
        output = ""
        for i in range(5):
            if g[i] == self.w[i]:
                output += "Y"
            elif g[i] not in self.w:
                output += "N"
            else:
                output += "~"
        return output

class WordleSolver:
    def __init__(self, cached_scores, word_set):
        self.cached_scores = cached_scores
        self.word_set = word_set
        self.update_y_idx()
        self.update_n_idx()
        self.update_nh_idx()
        self.first_guess = True
    
    def prune_idxs(self, guessed_word, response):
        # Prune Actual Word Vals
        for i in range(5):
            word_char = guessed_word[i]
            return_string_char = response[i]
            if return_string_char == 'Y':
                to_update = self.y_idx[i][word_char]
            elif return_string_char == '~':
                to_update = self.nh_idx[i][word_char]
            else:
                to_update = self.n_idx[word_char]
            self.word_set = self.word_set.intersection(to_update)
        self.update_y_idx()
        self.update_n_idx()
        self.update_nh_idx()
        
    def update_y_idx(self):
        self.y_idx = [{chr(c):set() for c in range(ord('a'), ord('z')+1)} for _ in range(5)]
        for w in self.word_set:
            for i in range(5):
                self.y_idx[i][w[i]].add(w)
    
    def update_n_idx(self):
        self.n_idx = {chr(c):set() for c in range(ord('a'), ord('z')+1)}
        for w in self.word_set:
            for ord_c in range(ord('a'), ord('z')+1):
                c = chr(ord_c) 
                if c not in w:
                    self.n_idx[c].add(w)
    
    def update_nh_idx(self):
        self.nh_idx = [{} for _ in range(5)]
        for ord_c in range(ord('a'), ord('z')+1):
            c = chr(ord_c)
            for i in range(5):
                to_add = set()
                for j in range(5):
                    if i != j:
                        to_add.update(self.y_idx[j][c])
                to_add = to_add - self.y_idx[i][c]
                self.nh_idx[i][c] = to_add
        
    
                
    def construct_scores(self):
        strings_to_evaluate = generate_all_return_strings(n=5)
        pruned = [s for s in strings_to_evaluate if is_valid_string(s)]
        self.cached_scores = {}
        n = len(self.word_set)
        for w in self.word_set:
            self.cached_scores[w] = expected_elims(
                w=w,
                yes_idx = self.y_idx,
                no_idx = self.n_idx,
                n_h_idx=self.nh_idx,
                total_words = n,
                pruned_strings=pruned
            )
    
    def make_guess(self):
        if len(self.word_set) == 1:
            for w in self.word_set:
                return w
        best_word = ""
        max_elims = 0
        for w in self.cached_scores:
            if self.cached_scores[w] > max_elims:
                max_elims = self.cached_scores[w]
                best_word = w
        return best_word
    
def play_k_games(k=10):
    word_set = build_set_of_words()
    with open('cached_scores.json') as f:
        cached_scores = json.load(f)
    sample_of_random_words = random.sample(word_set,k=k)
    for w in sample_of_random_words:
        wordle_game = Wordle(w)
        wordle_guesser = WordleSolver(cached_scores,word_set)
        r = ""
        num_guesses = 0
        while r != "Y"*5:
            reasoned_guess = wordle_guesser.make_guess()
            r = wordle_game.guess(reasoned_guess)
            num_guesses += 1
            print("Made Guess: {} w/ Response: {}".format(reasoned_guess,r))
            if r != "Y"*5:
                wordle_guesser.prune_idxs(reasoned_guess,r)
                wordle_guesser.construct_scores()
        print("Correct: {}. This was found in {} guesses.".format(reasoned_guess, num_guesses))

if __name__ == '__main__':
    play_k_games()

    
            
    