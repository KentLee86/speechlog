import importlib.util
from pathlib import Path
import subprocess
import sys
import pytest

SCRIPTS=Path(__file__).resolve().parents[1]/'scripts'
sys.path.insert(0,str(SCRIPTS))
import versioning
import release

@pytest.fixture
def repo(tmp_path):
    subprocess.run(['git','init','-b','main',str(tmp_path)],check=True,capture_output=True)
    subprocess.run(['git','config','user.email','synthetic@example.invalid'],cwd=tmp_path,check=True)
    subprocess.run(['git','config','user.name','Synthetic'],cwd=tmp_path,check=True)
    p=tmp_path/versioning.VERSION_PATH; p.parent.mkdir(parents=True); p.write_text('__version__ = "0.1.0"\n')
    (tmp_path/'pyproject.toml').write_text('dynamic = ["version"]\n[tool.hatch.version]\npath = "src/speechlog/_version.py"\n')
    (tmp_path/'.gitignore').write_text('dist/\n')
    (tmp_path/'CHANGELOG.md').write_text('# 변경 기록\n\n## 0.1.0\n\n가상 릴리스\n')
    subprocess.run(['git','add','.'],cwd=tmp_path,check=True)
    subprocess.run(['git','commit','-m','Synthetic fixture'],cwd=tmp_path,check=True,capture_output=True)
    subprocess.run(['git','remote','add','origin','https://github.com/KentLee86/speechlog.git'],cwd=tmp_path,check=True)
    return tmp_path

@pytest.mark.parametrize('target,expected',[('major','1.0.0'),('minor','0.2.0'),('patch','0.1.1'),('2.3.4','2.3.4')])
def test_semver_bump(target,expected):
    assert versioning.next_version('0.1.0',target)==expected

@pytest.mark.parametrize('target',['0.1.0','0.0.9','01.2.3','1.2','1.2.3-beta','bad'])
def test_invalid_version(target):
    with pytest.raises(ValueError): versioning.next_version('0.1.0',target)

def test_dry_run_and_dirty_guards(repo):
    assert versioning.bump(repo,'minor',True)['next']=='0.2.0'
    assert versioning.version(repo)=='0.1.0'
    assert release.plan(repo)['tag']=='v0.1.0'
    assert versioning.run(repo,'git','tag','--list')==''
    versioning.bump(repo,'minor')
    assert versioning.version(repo)=='0.2.0'
    with pytest.raises(ValueError,match='깨끗'): versioning.bump(repo,'patch',True)
    with pytest.raises(ValueError,match='깨끗'): release.plan(repo)

def test_single_source_and_release_guards(repo):
    (repo/'pyproject.toml').write_text('version = "0.1.0"\n')
    with pytest.raises(ValueError,match='dynamic'): versioning.version(repo)


def test_existing_tag_guard(repo):
    subprocess.run(['git','tag','v0.1.0'],cwd=repo,check=True)
    with pytest.raises(ValueError,match='이미 존재'): release.plan(repo)

def test_runtime_version_single_source():
    from speechlog import __version__
    assert __version__==versioning.version(SCRIPTS.parent)
    result=subprocess.check_output([sys.executable,'-m','speechlog','--version'],text=True).strip()
    assert result==f'speechlog {__version__}'


def test_publish_validates_then_passes_exact_tag_and_assets(repo,monkeypatch):
    import zipfile
    real_run=subprocess.run
    calls=[]
    def fake_run(argv,**kwargs):
        if argv[0]=='uv':
            calls.append(argv)
            if argv[1]=='build':
                dist=repo/'dist'; dist.mkdir()
                with zipfile.ZipFile(dist/'speechlog-0.1.0-py3-none-any.whl','w') as z:
                    z.writestr('speechlog-0.1.0.dist-info/METADATA','Version: 0.1.0\n')
                (dist/'speechlog-0.1.0.tar.gz').write_bytes(b'synthetic')
            return subprocess.CompletedProcess(argv,0)
        if argv[:2] in (['git','tag'],['git','push']) or argv[0]=='gh':
            calls.append(argv)
            if argv[0]=='gh':
                assert Path(argv[argv.index('--notes-file')+1]).read_text()=='가상 릴리스'
            return subprocess.CompletedProcess(argv,0)
        return real_run(argv,**kwargs)
    monkeypatch.setattr(subprocess,'run',fake_run)
    p=release.plan(repo)
    release.publish(repo,p)
    assert calls[:2]==[['uv','run','pytest','-q'],['uv','build']]
    assert calls[2]==['git','tag','-a','v0.1.0','-m','speechlog 0.1.0',p['commit']]
    assert calls[3:5]==[['git','push','origin','HEAD:main'],['git','push','origin','v0.1.0']]
    assert calls[5][:4]==['gh','release','create','v0.1.0']
    assert calls[5][4:6]==[str(repo/'dist/speechlog-0.1.0-py3-none-any.whl'),str(repo/'dist/speechlog-0.1.0.tar.gz')]
    assert '--verify-tag' in calls[5]
