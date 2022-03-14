word_1 = input()
word_2 = input()

for letter_1, letter_2 in zip(word_1, word_2):
    print(letter_1 + letter_2, end="")
