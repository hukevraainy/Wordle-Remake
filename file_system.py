import os
import random
import time 
from structures import LinkedList

# paths
DATA_DIR = "assets/data/" 
WORDS_FILE = DATA_DIR + "words.txt"
USERS_FILE = DATA_DIR + "users.bin"
SESSIONS_FILE = DATA_DIR + "sessions.bin"
TIME_STATS_FILE = DATA_DIR + "time_stats.bin"

# simple XOR encryption key
XOR_KEY = 157

def ensure_data_dir():
    # ensure data directory exists
    try:
        # check if possible to write a test file to the directory
        with open(DATA_DIR + ".exists", 'w') as f:
            f.write("test")
    except FileNotFoundError:
        # if the directory doesn't exist, notify the user
        print(f"Critical Error: Folder {DATA_DIR} not found. Please create it manually.")

def custom_encrypt(text):
    return bytearray([b ^ XOR_KEY for b in text.encode('utf-8')])

def custom_decrypt(data):
    return bytearray([b ^ XOR_KEY for b in data]).decode('utf-8')

# word management
def load_words():
    data = {}
    try:
        with open(WORDS_FILE, 'r') as f:
            for line in f:
                parts = line.strip().split('|')
                if len(parts) == 3:
                    cat = parts[0]
                    diff = int(parts[1])
                    word_list = parts[2].split(',')
                    data[cat] = {"diff": diff, "words": word_list}
    except FileNotFoundError: 
        return {}
    return data

def get_standard_word():
    data = load_words()
    all_words = []
    for cat in data: all_words.extend(data[cat]['words'])
    if not all_words: return "ERROR", 6
    return random.choice(all_words).upper(), 6

def get_random_word(category):
    data = load_words()
    if category not in data: return None, 6
    words = data[category]['words']
    return random.choice(words).upper(), data[category]['diff']

def get_random_mix():
    data = load_words()
    if not data: return "ERROR", "ERROR", 6
    cats = list(data.keys())
    random_cat = random.choice(cats)
    word_list = data[random_cat]['words']
    difficulty = data[random_cat]['diff']
    target_word = random.choice(word_list).upper()
    return random_cat, target_word, difficulty


# change word every day at midnight UTC
def get_timed_word():
    data = load_words()
    all_words = []
    for cat in data:
        all_words.extend(data[cat]['words'])
        
    if not all_words: 
        return "ERROR", 6
    
    # calculate the number of days since epoch
    interval_index = int(time.time() // 86400)
    
    # use the interval as a seed for consistent randomization
    random.seed(interval_index)
    target = random.choice(all_words).upper()
    
    # reset seed to system time
    random.seed() 
    
    return target, 6

# time attack stats management
def save_time_score(duration, score, username):
    # saves a new time attack score and trims to top 20
    ensure_data_dir()
    
    # 1. load all current records into a list of dictionaries
    all_records = []
    try:
        with open(TIME_STATS_FILE, 'rb') as f:
            content = custom_decrypt(f.read())
            if content:
                parts = content.split('|')
                for p in parts:
                    if ':' in p:
                        segments = p.split(':')
                        if len(segments) >= 3:
                            all_records.append({
                                'dur': segments[0],
                                'score': int(segments[1]),
                                'name': segments[2]
                            })
    except (FileNotFoundError, IOError):
        pass

    # 2. add the new record
    all_records.append({
        'dur': str(duration),
        'score': score,
        'name': username
    })

    # 3. sort by score (descending) and then duration (descending)
    all_records.sort(key=lambda x: (x['score'], int(x['dur'])), reverse=True)

    # 4. limit to 20 accounts
    top_20 = all_records[:20]

    # 5. serialize and save, format: "dur:score:name|dur:score:name"
    lines = [f"{r['dur']}:{r['score']}:{r['name']}" for r in top_20]
    full_text = "|".join(lines)
    
    try:
        with open(TIME_STATS_FILE, 'wb') as f:
            f.write(custom_encrypt(full_text))
    except IOError:
        print("Error saving Time Attack leaderboard.")

def load_time_stats_list():
    #returns a sorted list of dictionaries for the leaderboard UI
    records = []
    try:
        with open(TIME_STATS_FILE, 'rb') as f:
            content = custom_decrypt(f.read())
            if not content: return []
            parts = content.split('|')
            for p in parts:
                segments = p.split(':')
                if len(segments) >= 3:
                    records.append({
                        'dur': segments[0],
                        'score': int(segments[1]),
                        'name': segments[2]
                    })
    except (FileNotFoundError, IOError):
        pass
    return records

def load_time_stats():
    # returns time stats as a dict for quick lookup
    stats = {}
    try:
        with open(TIME_STATS_FILE, 'rb') as f:
            content = custom_decrypt(f.read())
            if not content: return {}
            parts = content.split('|')
            for p in parts:
                if ':' in p:
                    segments = p.split(':')
                    # safety check for format
                    if len(segments) >= 2:
                        k = segments[0]
                        try:
                            v = int(segments[1])
                            name = segments[2] if len(segments) > 2 else "Unknown"
                            stats[k] = {'score': v, 'name': name}
                        except ValueError:
                            print(f"Skipping corrupt stat: {p}")
    except (FileNotFoundError, IOError): 
        pass
    return stats

# user and session management
def parse_user_str(line):
    # parse encrypted file into dictionary
    d = {}
    if not line: return None
    
    parts = line.split('|')
    for part in parts:
        if ':' in part:
            k, v = part.split(':', 1)
            
            # number conversions
            if k in ['avg_time', 'total_time']:
                try: d[k] = float(v)
                except ValueError: d[k] = 0.0
            elif k == 'games':
                try: d[k] = int(v)
                except ValueError: d[k] = 0
            
            # history field mapping: 
            # ensure keys used in parse ('word', 'guesses') match the keys used in 'save_users'
            elif k == 'word': d['last_word'] = v
            elif k == 'guesses': d['last_guesses'] = v
            else: d[k] = v
            
    return d

def save_users(ll):
    # saves linked list of users to encrypted file
    lines = []
    curr = ll.head
    while curr:
        d = curr.data
        line = (f"name:{d['name']}|avg_time:{d['avg_time']}|games:{d['games']}|"
                f"total_time:{d['total_time']}|word:{d.get('last_word', 'N/A')}|"
                f"guesses:{d.get('last_guesses', '')}")
        lines.append(line)
        curr = curr.next
        
    try:
        with open(USERS_FILE, 'wb') as f: 
            f.write(custom_encrypt("\n".join(lines)))
    except IOError:
        print("Error: Could not save match history to users.bin")

def load_users():
    ll = LinkedList()
    try:
        with open(USERS_FILE, 'rb') as f:
            content = custom_decrypt(f.read())
        for line in content.split('\n'):
            if line:
                d = parse_user_str(line)
                if d: ll.add_sorted(d)
    except FileNotFoundError: pass
    return ll

def get_session_users():
    users = []
    try:
        with open(SESSIONS_FILE, 'rb') as f:
            content = custom_decrypt(f.read())
            for line in content.split('\n'):
                parts = line.split('|')
                if len(parts) >= 1 and parts[0]: users.append(parts[0])
    except: pass
    return users

def save_session(username, state, overwrite_target=None):
    # saves or updates player's session in the file
    ensure_data_dir()
    all_sessions = {}
    try:
        with open(SESSIONS_FILE, 'rb') as f:
            content = custom_decrypt(f.read())
            for line in content.split('\n'):
                parts = line.split('|')
                if len(parts) >= 4: all_sessions[parts[0]] = line
    except: pass

    if username not in all_sessions and len(all_sessions) >= 5 and overwrite_target is None:
        return False

    if overwrite_target and overwrite_target in all_sessions:
        del all_sessions[overwrite_target]

    guesses_str = ",".join(state['guesses'])
    new_line = f"{username}|{state['target']}|{guesses_str}|{state['category']}"
    all_sessions[username] = new_line
    
    try:
        with open(SESSIONS_FILE, 'wb') as f:
            f.write(custom_encrypt("\n".join(all_sessions.values())))
        return True
    except: return False

def delete_session(username):
    # removes a user's session from the file after they finish a game
    all_sessions = {}
    try:
        with open(SESSIONS_FILE, 'rb') as f:
            content = custom_decrypt(f.read())
            for line in content.split('\n'):
                parts = line.split('|')
                if len(parts) >= 4:
                    all_sessions[parts[0]] = line
    except:
        return

    if username in all_sessions:
        del all_sessions[username]
        
        # write back the remaining sessions
        full_text = "\n".join(all_sessions.values())
        try:
            with open(SESSIONS_FILE, 'wb') as f:
                f.write(custom_encrypt(full_text))
        except IOError:
            print(f"Error clearing session for {username}")

def load_session(username):
    # loads a user's session from the file
    try:
        with open(SESSIONS_FILE, 'rb') as f:
            content = custom_decrypt(f.read())
        for line in content.split('\n'):
            parts = line.split('|')
            if len(parts) >= 4 and parts[0] == username:
                return {"target": parts[1], "guesses": parts[2].split(',') if parts[2] else [], "category": parts[3]}
    except: pass
    return None