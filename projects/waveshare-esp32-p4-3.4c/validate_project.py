"""按依赖顺序执行工程检查，统一UTF-8日志，失败立即停止。"""
import json
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parent


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    out=ROOT/'output'
    stages=[('fit','verify_fit.py'),('walls','verify_walls.py'),
        ('slice','verify_print.py','--slice','--material','PETG'),
        ('render','render_previews.py'),('unit','-m','unittest','test_slicing'),
        ('readiness','verify_readiness.py')]
    state=[]
    for name,*command in stages:
        print('执行',name,flush=True)
        log=out/(name+'_console.log')
        with log.open('w',encoding='utf-8') as stream:
            result=subprocess.run([sys.executable,'-X','utf8',*command],cwd=ROOT,
                stdout=stream,stderr=subprocess.STDOUT)
        state.append({'stage':name,'returncode':result.returncode,'log':log.name})
        (out/'pipeline_validation.json').write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf-8')
        if result.returncode:
            print(log.read_text(encoding='utf-8')[-4000:],flush=True)
            return result.returncode
        print(name,'通过',flush=True)
    return 0


if __name__=='__main__':
    raise SystemExit(main())
