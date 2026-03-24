import subprocess, os

files = ['scientist/tsp/__init__.py', 'scientist/tsp/prepare.py', 'scientist/tsp/program.md', 'scientist/tsp/archive/original.py']
baselines = ['berlin52.tsp', 'ch150.tsp', 'eil51.tsp', 'kroA100.tsp', 'st70.tsp']

os.makedirs('scientist/tsp/baselines', exist_ok=True)
os.makedirs('scientist/tsp/archive', exist_ok=True)

for f in files:
    content = subprocess.check_output(['git', 'show', f'HEAD:{f}'])
    with open(f, 'wb') as fh:
        fh.write(content)
    print(f'restored {f}')

for b in baselines:
    f = f'scientist/tsp/baselines/{b}'
    content = subprocess.check_output(['git', 'show', f'HEAD:{f}'])
    with open(f, 'wb') as fh:
        fh.write(content)
    print(f'restored {f}')

print('Done')
