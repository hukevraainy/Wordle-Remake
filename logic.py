def check_guess(guess, target):
    # execute the main logic of comparing guess to target
    # returns list: 2:Green, 1:Yellow, 0:Gray
    res = [0] * 5
    target_counts = {}
    
    # count frequency of each char in target
    for char in target:
        target_counts[char] = target_counts.get(char, 0) + 1
        
    # green pass
    for i in range(5):
        if guess[i] == target[i]:
            res[i] = 2
            target_counts[guess[i]] -= 1
            
    # yellow pass
    for i in range(5):
        if res[i] == 0 and guess[i] in target_counts and target_counts[guess[i]] > 0:
            res[i] = 1
            target_counts[guess[i]] -= 1
            
    return res