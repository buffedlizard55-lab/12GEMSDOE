import subprocess,pathlib,concurrent.futures,json,hashlib
base=pathlib.Path(__file__).resolve().parents[1]; root=base/'data'; root.mkdir(exist_ok=True); m=json.load(open(base/'evidence/bridge-manifest.json'))
rev='cceebbdcf9a7d2890bb0665defcb54dfc66ae452'; print(rev,flush=True)
(root/'bridge-revision.txt').write_text(rev)
jobs=[]
for f in m['files']:
 for p in f.get('parts',[f]):jobs.append(p)
def get(p):
 dest=root/p['name'];
 if dest.exists() and hashlib.sha256(dest.read_bytes()).hexdigest()==p['sha256']: return
 cmd=['gh','api',f'repos/buffedlizard55-lab/GEMSDOE/contents/data/bridge/{p["name"]}?ref={rev}','-H','Accept: application/vnd.github.raw']
 with dest.open('wb') as o:subprocess.run(cmd,stdout=o,check=True)
 assert hashlib.sha256(dest.read_bytes()).hexdigest()==p['sha256'],p
 print('verified',p['name'],flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as e:list(e.map(get,jobs))
for f in m['files']:
 dest=root/f['canonical']
 with dest.open('wb') as o:
  for p in f.get('parts',[f]):
   with (root/p['name']).open('rb') as i:
    while b:=i.read(1024*1024):o.write(b)
 assert hashlib.sha256(dest.read_bytes()).hexdigest()==f['sha256']
 print('assembled',dest,flush=True)
