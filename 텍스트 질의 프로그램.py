import re
from collections import Counter, defaultdict

STOPWORDS = {'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', 'youre', 'youve',
            'youll', 'youd', 'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 'himself',
            'she', 'shes', 'her', 'hers', 'herself', 'it', 'its', 'itself', 'they', 'them', 
            'their', 'theirs', 'themselves', 'what', 'which', 'who', 'whom', 'this', 'that', 'thatll', 
            'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has',
            'had', 'having', 'do', 'does', 'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if', 'or', 
            'because', 'as', 'until', 'while', 'of', 'at', 'by', 'for', 'with', 'about', 'against', 'between', 
            'into', 'through', 'during', 'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down', 'in', 
            'out', 'on', 'off', 'over', 'under', 'again', 'further', 'then', 'once', 'here', 'there', 'when', 
            'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 
            'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'can', 'will', 'just', 
            'don', 'dont', 'should', 'shouldve', 'now', 'd', 'll', 'm', 'o', 're', 've', 'y', 'ain', 'aren', 'arent', 
            'couldn', 'couldnt', 'didn', 'didnt', 'doesn', 'doesnt', 'hadn', 'hadnt', 'hasn', 'hasnt', 'haven', 
            'havent', 'isn', 'isnt', 'ma', 'mightn', 'mightnt', 'mustn', 'mustnt', 'needn', 'neednt', 'shan', 'shant', 
            'shouldn', 'shouldnt', 'wasn', 'wasnt', 'weren', 'werent', 'won', 'wont', 'wouldn', 'wouldnt'}

query = " "
file = input("Please enter file name: ")

f=open(file,'r',encoding="utf-8")

lines = f.readlines()
all_lines = set(range(1, len(lines) + 1))

counter = Counter()
index = defaultdict(set)

for num, line in enumerate(lines, start=1) : 
    words = re.sub(r"[^a-z0-9가-힣\s]", " ", line.lower().strip()).split()
    words = [word for word in words if word not in STOPWORDS]
    counter.update(words)

    for word in words:
        index[word].add(num)

while query != ".":
    print("Enter a word against which to search the text.")
    query = input("To quit, enter a single character = = => ")
    
    if query == ".":
        print("Ok, bye!")
        break;

    tokens = re.findall(r'\w+|&&|\|\||!|\(|\)', query.lower())

    stack = []

    def evaluate(t):
        while "!" in t:
            pos = t.index("!")
            t[pos:pos+2] = [all_lines - t[pos+1]]
            
        if len(t) == 1:
            result = t[0]
    
        if len(t) == 3 and t[1] == "&&":
            result = t[0] & t[2]
    
        if len(t) == 3 and t[1] == "||":
            result = t[0] | t[2]
        return result

    for token in tokens:
        if token not in ["&&", "||", "!", "(", ")"]:
            stack.append(index[token])
        else :
            stack.append(token) 
        
        if stack[-1] == ")":
            stack.pop()
            t = []
            while stack[-1] != "(":
                t.append(stack.pop())
            stack.pop()
            t.reverse()
            stack.append(evaluate(t))
    result = evaluate(stack)



    if len(result) == 0:
        print(f"Sorry. There are no entries for {query}.")
    else: 
        if len(tokens) == 1:
            print(f"{query} occurs {counter[query]} times:")
        else: 
            print(f"{query} matches {len(result)} line(s):")

        for num in sorted(result):
            print(f"( line {num} ) {lines[num - 1].strip()}")
        

    