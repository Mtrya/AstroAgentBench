from experiments.evaluate.prepare import prepare, tree_hash
from experiments.evaluate.workspace import SOLUTION_MOUNT, build_command, image_tag, run_command


def flag_value(cmd, flag):
    return cmd[cmd.index(flag) + 1]


def env_value(cmd, name):
    prefix = f'{name}='
    return next(part[len(prefix):] for part in cmd if part.startswith(prefix))


def test_image_tag_changes_with_case_contents():
    base = image_tag('spot5', 'test', '8', 'a' * 64)
    assert base == image_tag('spot5', 'test', '8', 'a' * 64)
    assert base != image_tag('spot5', 'test', '8', 'b' * 64)
    assert base != image_tag('spot5', 'test', '9', 'a' * 64)
    assert base == 'astroagentbench/workspace-spot5-test-8-' + 'a' * 12


def test_image_tag_replaces_characters_docker_rejects():
    assert image_tag('regional coverage', 'test', 'case/0001', 'c' * 64) == (
        'astroagentbench/workspace-regional-coverage-test-case-0001-' + 'c' * 12
    )


def test_image_tag_lowercases_identifiers_docker_rejects(tmp_path):
    assert prepare('satnet', 'test', 'W20_2018', tmp_path / 'case').is_dir()
    assert image_tag('satnet', 'test', 'W20_2018', 'd' * 64) == (
        'astroagentbench/workspace-satnet-test-w20_2018-' + 'd' * 12
    )


def test_image_tag_separates_base_images(tmp_path):
    default = prepare('spot5', 'test', '8', tmp_path / 'default')
    custom = prepare('spot5', 'test', '8', tmp_path / 'custom', image='custom:tag')
    built = (tree_hash(task / 'environment') for task in (default, custom))
    default_hash, custom_hash = built
    assert default_hash != custom_hash
    assert image_tag('spot5', 'test', '8', default_hash) != image_tag('spot5', 'test', '8', custom_hash)


def test_interactive_run_allocates_a_tty_and_starts_a_shell(tmp_path):
    cmd = run_command('tag', tmp_path, cpus=2, memory_mb=4096, network='public')
    assert cmd[:5] == ['docker', 'run', '--rm', '-i', '-t']
    assert cmd[-1] == 'bash'


def test_explicit_command_runs_headless(tmp_path):
    cmd = run_command('tag', tmp_path, cpus=2, memory_mb=4096, network='public', command=['bash', '-c', 'ls'])
    assert '-i' not in cmd
    assert '-t' not in cmd
    assert cmd[-3:] == ['bash', '-c', 'ls']


def test_run_applies_declared_limits_and_network_policy(tmp_path):
    public = run_command('tag', tmp_path, cpus=3, memory_mb=3072, network='public')
    assert flag_value(public, '--cpus') == '3'
    assert flag_value(public, '--memory') == '3072m'
    assert flag_value(public, '--workdir') == '/workspace'
    assert '--network' not in public
    offline = run_command('tag', tmp_path, cpus=3, memory_mb=3072, network='no-network')
    assert flag_value(offline, '--network') == 'none'


def test_run_mounts_the_solution_directory_and_binds_host_identity(tmp_path):
    solution = tmp_path / 'solution'
    solution.mkdir()
    cmd = run_command('tag', solution, cpus=2, memory_mb=4096, network='public')
    assert flag_value(cmd, '-v') == f'{solution.resolve()}:{SOLUTION_MOUNT}'
    uid, _, gid = flag_value(cmd, '--user').partition(':')
    assert uid.isdigit() and gid.isdigit()
    assert env_value(cmd, 'HOME') == '/tmp'
    assert env_value(cmd, 'USER')
    assert env_value(cmd, 'LOGNAME') == env_value(cmd, 'USER')


def test_build_command_uses_the_prepared_environment_context(tmp_path):
    context = tmp_path / 'environment'
    context.mkdir()
    assert build_command('tag', context) == ['docker', 'build', '-t', 'tag', str(context)]