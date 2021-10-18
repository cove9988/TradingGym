import os
import datetime

file = "VERSION"
key = "__version__="
comment=''
m =0
with open(file, "r+") as f:
    lines = f.read()
    if key in lines:
        v = float(lines.replace(key, "").replace("\n", ""))
        v = round(v + 0.1, 1)
        f.seek(0)
        lines =f'{key}{v}'
        print(f'bump to: {lines}\n')
        f.write(lines)
        f.truncate()
    else:
        print("Not right version __init__ file")