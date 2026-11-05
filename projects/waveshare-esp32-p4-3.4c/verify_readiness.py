"""汇总当前产物绑定与待实测项目；空值绝不视为已通过。"""
import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
FIELDS={
    'hardware_frozen':None,'battery_discharge_rating_verified':None,
    'charge_current_setting_verified':None,'cell_temperature_protection_verified':None,
    'panel_usb_switch_and_wiring_verified':None,'speaker_mount_and_isolation_verified':None,
    'runtime_minutes':None,'runtime_conditions_verified':None,'usb_transfer_no_restart':None,
    'five_assembly_cycles_pass':None,'touch_3n_pass':None,'thermal_2h_pass':None,
    'wake_quiet_pass':None,'wake_playing_aec_pass':None,
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(out):
    summary=json.loads((out/'validation.json').read_text(encoding='utf-8'))
    checks={'source_hash':summary['source_sha256']==digest(ROOT/'enclosure.py')}
    for name,expected in summary['artifacts'].items():
        checks['artifact_'+name]=digest(out/name)==expected
    for name,part in summary['parts'].items():
        checks['stl_'+name]=digest(out/'trials'/(name+'.stl'))==part['sha256']
    fit_path=out/'fit_validation.json'
    fit=json.loads(fit_path.read_text(encoding='utf-8')) if fit_path.exists() else {}
    checks['fit_passed']=fit.get('passed') is True and fit.get('hashes',{}).get('source')==summary['source_sha256']
    checks['fit_fcstd_current']=fit.get('hashes',{}).get('fcstd')==digest(out/'enclosure.FCStd')
    checks['fit_step_current']=fit.get('hashes',{}).get('step')==digest(out/'enclosure.step')
    revision_path=out/'revision_validation.json'
    revision=json.loads(revision_path.read_text(encoding='utf-8')) if revision_path.exists() else {}
    checks['seven_parts_compatible']=(revision.get('passed') is True
        and revision.get('source_sha256')==summary['source_sha256']
        and revision.get('fcstd_sha256')==digest(out/'enclosure.FCStd'))
    wall_path=out/'wall_validation.json'
    walls=json.loads(wall_path.read_text(encoding='utf-8')) if wall_path.exists() else {}
    checks['wall_samples']=(walls.get('passed') is True
        and walls.get('source_sha256')==summary['source_sha256']
        and walls.get('fcstd_sha256')==digest(out/'enclosure.FCStd'))
    printing_path=out/'print_validation.json'
    printing=json.loads(printing_path.read_text(encoding='utf-8')) if printing_path.exists() else {}
    checks['reference_slicing']=printing.get('reference_slicing_verified') is True
    checks['eight_print_parts']=len(summary['parts'])==8
    for name in summary['parts']:
        path=out/(name+'_petg_print_validation.json')
        r=json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
        checks['petg_'+name]=(r.get('reference_slice_passed') is True
            and r.get('stl_sha256')==summary['parts'][name]['sha256']
            and r.get('verification_source_sha256')=={
                p:digest(ROOT/p) for p in ('verify_print.py','print_audit.py')})
        cache=ROOT/r['cache'] if r.get('cache') else None
        checks['gcode_'+name]=bool(cache and (cache/'plate_1.gcode').exists()
            and digest(cache/'plate_1.gcode')==r.get('gcode_sha256'))
    path=out/'hardware_measurements.json'
    measurements=json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
    for field,value in FIELDS.items():
        measurements.setdefault(field,value)
    measurements['schema']=summary['schema']
    path.write_text(json.dumps(measurements,ensure_ascii=False,indent=2),encoding='utf-8')
    pending=[field for field in FIELDS if field!='runtime_minutes' and measurements[field] is not True]
    minutes=measurements['runtime_minutes']
    if not isinstance(minutes,(int,float)) or isinstance(minutes,bool) or minutes<60:
        pending.append('runtime_minutes_at_least_60')
    result={'schema':summary['schema'],'engineering_checks':checks,
        'engineering_candidate_verified':all(checks.values()),'pending_physical_checks':pending,
        'physical_acceptance_passed':not pending,
        'production_ready':False,
        'note':'候选源文件始终拒绝--release；正式定型需另行审查真实硬件、实测证据与打印版本。'}
    (out/'readiness_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=ROOT/'output')
    args=parser.parse_args()
    result=verify(args.out.resolve())
    raise SystemExit(0 if result['engineering_candidate_verified'] else 1)
