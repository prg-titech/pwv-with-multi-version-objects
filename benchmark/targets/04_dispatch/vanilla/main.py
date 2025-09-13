import time, random
TIMES = 100
class Array:
    def __init__(self, values):
        self.values = values

    def sort(self):
        if len(self.values) <= 1:
            return self
        
        pivot = self.values[0]

        lower = []
        upper = []
        
        for x in self.values[1:]:
            if x <= pivot:
                lower.append(x)
            else:
                upper.append(x)
        
        sorted_lower = Array(lower).sort()
        sorted_upper = Array(upper).sort()
        
        sorted_array = sorted_lower.values + [pivot] + sorted_upper.values
        
        return Array(sorted_array)

def main():
    random_nums = [random.randint(0, 100) for _ in range(1000)]
    my_array = Array(random_nums)
    
    start_time = time.perf_counter()
    for _ in range(TIMES):
        my_array.sort()
    end_time = time.perf_counter()
    avg_time = (end_time - start_time) / TIMES
    
    print(avg_time)

if __name__ == "__main__":
    main()
