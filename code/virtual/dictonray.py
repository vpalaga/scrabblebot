import bisect

with open("/home/vpalaga/orgs/vp/sb/virtual/save.txt", "r") as f:
    # Read lines from the file directly
    dictionary_list = [line.strip() for line in f]
    # Make sure your file is sorted. If not certain, do:
    dictionary_list.sort()

class Us_en:
    def __init__(self):
        self.dictionary = dictionary_list
    
    def check(self, word: str) -> bool:
        """
        Return True if 'word' exists in the sorted dictionary list,
        using binary search for O(log n) membership.
        """
        idx = bisect.bisect_left(self.dictionary, word)
        return idx < len(self.dictionary) and self.dictionary[idx] == word

if __name__ == "__main__":
    d = Us_en()
    print(d.check("metronome"))
