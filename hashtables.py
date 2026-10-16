HASH_SIZE = 11

class AccountHashTable:
    def __init__(self, size=HASH_SIZE):
        self.size = size
        self.buckets = [None] * size

    def _hash(self, acc_num):
        return acc_num % self.size

    def insert(self, node):
        idx = self._hash(node.account_number)
        node.next = self.buckets[idx]
        self.buckets[idx] = node

    def search(self, acc_num):
        cur = self.buckets[self._hash(acc_num)]
        while cur:
            if cur.account_number == acc_num:
                return cur
            cur = cur.next
        return None