with open('log.txt', 'r') as inp, open('fmt_log.txt', 'w') as out: 
    for line in inp:
        out.write(line.replace('[FireP', '\nFireP').replace(', FireP', '\nFireP').replace(']', '\n').replace(
            'radius=0.375', 'radius=0.375)').replace('radius=1', 'radius=1)'))
