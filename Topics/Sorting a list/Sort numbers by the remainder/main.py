nums = [int(num) for num in list(input())]

nums.sort(key=lambda x: x % 3)
print(nums)
