"""Configures all tasks to run with invoke."""

from invoke import task
import glob
import os
import fnmatch


@task(
    default=True,
    help={
        'warnings': 'Warning configuration, as described at https://docs.python.org/2/using/cmdline.html#cmdoption-W \
        for example, to disable Deprecation',
        'filename': 'Path to template(s) to `compile`. Supports globbing.',
        'args': 'Additional arguments to pass to template file.'
                ' Multiple arguments should each be specified with a new --args flag, ie. `invoke build --args foo --args bar`.',
    },
    iterable=['args'],
)
def build(ctx, warnings='once::DeprecationWarning', filename=None, args=None):
    """Build all templates."""
    import sys
    import subprocess
    import inspect
    if filename is not None:
        templates = [x for x in glob.glob(filename)]
        if len(templates) == 0:
            print("File `{0}` not found".format(filename))
            exit(1)
    else:
        print("Building all templates")
        os.chdir(os.path.dirname(os.path.abspath(inspect.stack()[0][1])))
        templates = [x for x in glob.glob('templates/*/*') if x[-3:] == '.py']

    rv = 0
    for template in templates:
        if not os.path.isfile(template):
            continue
        print(" + Executing {0}{1}".format(template, f" with arguments {args}" if args else ""))
        if subprocess.call([sys.executable, '-W{0}'.format(warnings), '{0}'.format(template)] + list(args)) != 0:
            rv = 1
    exit(rv)


@task(help={
    'verbose': "Show which files are being removed.",
    'compiled': 'Also clean up compiled python files.',
})
def clean(ctx, verbose=False, compiled=False):
    """Clean up all output files."""
    command = "rm -rvf {files}" if verbose else "rm -rf {files}"

    patterns = []
    patterns.append('output/*.json')
    patterns.append('output/*/*.json')
    if compiled is True:
        for root, dirnames, filenames in os.walk('.'):
            for filename in fnmatch.filter(filenames, '*.pyc'):
                patterns.append(os.path.join(root, filename))

    for pattern in patterns:
        ctx.run(command.format(files=pattern))


@task(
    aliases=["flake8", "pep8"],
    help={
        'filename': 'File(s) to lint. Supports globbing.',
        'envdir': 'Specify the python virtual env dir to ignore. Defaults to "venv".',
        'noglob': 'Disable globbing of filenames. Can give issues in virtual environments',
    },
)
def lint(ctx, filename=None, envdir='venv', noglob=False):
    """Run flake8 python linter."""
    command = 'flake8 --jobs=1 --exclude .git,' + envdir

    if filename is not None:
        if noglob:
            templates = [filename]
        else:
            templates = [x for x in glob.glob(filename)]
            if len(templates) == 0:
                print("File `{0}` not found".format(filename))
                exit(1)

        command += ' ' + " ".join(templates)

    print("Running command: '" + command + "'")
    ctx.run(command)


@task(
    help={
        'filename': 'File(s) to lint. Supports globbing.',
    },
)
def validate(ctx, filename=None):
    """Validate the output file(s)."""
    exclude = ['bcm_mapping', 'ec2_profile']
    command = 'aws-cfn-validate '
    if filename is not None:
        command += '{filename} '.format(filename=filename)
    else:
        command += 'output/*/*.json '

    command += ' '.join(['--exclude {0}'.format(x) for x in exclude])
    ctx.run(command)


@task(
    help={
        'filename': 'Path to template(s) to process. Supports globbing.',
        'envdir': 'Specify the python virtual env dir to ignore. Defaults to "venv".',
        'noglob': 'Disable globbing of filenames. Can give issues in virtual environments',
        'warnings': 'Warning configuration, as described at https://docs.python.org/3/using/cmdline.html#cmdoption-W'
                    ' for example, to disable Deprecation',
        'args': 'Additional arguments to pass to template file.'
                ' Multiple arguments should each be specified with a new --args flag, ie. `invoke process --args foo --args bar`.',
    },
    iterable=['args'],
)
def process(ctx, filename=None, envdir='venv', noglob=False, warnings='once::DeprecationWarning', args=None):
    """Run lint and build commands for specified template(s)."""
    lint(ctx, filename, envdir, noglob)
    build(ctx, warnings, filename, args)
