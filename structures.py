class Node:
    def __init__(self, data):
        self.data = data
        self.next = None

class LinkedList:
    # stores top-20 based on avg time
    def __init__(self):
        self.head = None
        self.size = 0

    def add_sorted(self, user_data):
        new_node = Node(user_data)
        
        # C1: Empty list/new user faster than head
        if self.head is None or user_data['avg_time'] < self.head.data['avg_time']:
            new_node.next = self.head
            self.head = new_node
        else:
            # C2: Find corrent pos
            current = self.head

            while current.next and current.next.data['avg_time'] <= user_data['avg_time']:
                current = current.next
            new_node.next = current.next
            current.next = new_node
        
        self.size += 1
        self.trim_to_20()

    def trim_to_20(self):
        # limits leaderboard to 20 players
        if self.size <= 20: return
        curr = self.head
        for _ in range(19): 
            if curr: curr = curr.next
        if curr: curr.next = None 
        self.size = 20

    def find_user(self, name):
        # find user data by name
        curr = self.head
        while curr:
            if curr.data['name'] == name:
                return curr.data
            curr = curr.next
        return None
        
    def to_list(self):
        # convert linked list to regular list
        result = []
        curr = self.head
        while curr:
            result.append(curr.data)
            curr = curr.next
        return result
    
    def remove_user(self, name):
        # removes all nodes with the matching username
        # returns True if at least one user was removed
        removed = False
        
        # head removal
        while self.head and self.head.data['name'] == name:
            self.head = self.head.next
            self.size -= 1
            removed = True
            
        # body removal
        current = self.head
        while current and current.next:
            if current.next.data['name'] == name:
                current.next = current.next.next
                self.size -= 1
                removed = True
            else:
                current = current.next
                
        return removed

class Stack:
    # undo/redo feature
    def __init__(self):
        self.top = None

    def push(self, data):
        node = Node(data)
        node.next = self.top
        self.top = node

    def pop(self):
        if not self.top: return None
        data = self.top.data
        self.top = self.top.next
        return data

    def is_empty(self):
        return self.top is None