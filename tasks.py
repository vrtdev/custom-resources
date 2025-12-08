"""Configures all tasks to run with invoke."""

from invoke import task
import glob
import os
import fnmatch


@task(
    help={
        'args': 'Additional arguments to pass to template file.'
                ' Multiple arguments should each be specified with a new --args flag, ie. `invoke build --args foo --args bar`.',
    },
    iterable=['args'],
)
def build(ctx, args=None):
    """Build all custom resources."""
    command = ["python", "build.py"]
    if args:
        command.extend(args)

    import subprocess
    subprocess.run(
        command,
        check=True,
    )


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
        'noglob': 'Disable globbing of filenames. Can give issues in virtual environments',
    },
)
def lint(ctx, filename=None, noglob=False):
    """Run flake8 python linter."""
    command = 'flake8 --jobs=1'

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
    default=True,
    help={
        'filename': 'Path to template(s) to process. Supports globbing.',
        'noglob': 'Disable globbing of filenames. Can give issues in virtual environments',
        'args': 'Additional arguments to pass to template file.'
                ' Multiple arguments should each be specified with a new --args flag, ie. `invoke process --args foo --args bar`.',
    },
    iterable=['args'],
)
def process(ctx, filename=None, noglob=False, args=None):
    """Run lint and build commands for specified template(s)."""
    # lint(ctx, filename, noglob)
    build(ctx, args)
