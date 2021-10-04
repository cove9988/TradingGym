import sys
n = 0
def output(input, original, pre):
    global n
    
    if len(original) in(0,1):
        #add last mapping to the string
        if len(original) == 1:
            pre += input.get(original[0:1])
        n += 1
        cm=[]
        for detail in pre:
            for x, y in input.items():
                if y == detail:
                    cm.append(detail + "=" + x )
        #list string wih mapping detail
        print (" %5d %s  ==> %s"%(n, pre, cm))
        return
    
    #if there are 2 digits mapping
    if input.get(original[0:2]) != None :
        new_chr = input.get(original[0:2])
        output(input, original[2:], pre + new_chr)
    
    #single digits mapping    
    new_chr = input.get(original[0:1])
    output(input, original[1:], pre + new_chr)

if __name__ == '__main__':
    sys.stdout = open('output.txt', 'wt') 
    starter = 0  #start mapping a -> 0 change to 1 if a ->;1
    input_mapping = {str(x):y for x in range(starter, starter+26) for y in chr(97 + x)}
    print("input mapping %s" %input_mapping)
    input = '234132598022231224433110010022'
    print ("your input : %s:" %input)
    output(input_mapping, input, '')