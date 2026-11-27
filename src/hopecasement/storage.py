from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from tempfile import NamedTemporaryFile


@contextmanager
def atomic_output(destination: Path, *, overwrite: bool = True) -> Iterator[Path]:
    """Publish a complete file, keeping the previous one if writing fails."""
    with NamedTemporaryFile(dir=destination.parent, delete=False) as file:
        temporary = Path(file.name)
    try:
        yield temporary
        if overwrite:
            temporary.replace(destination)
        else:
            temporary.rename(destination)  # Windows rejects a target created in the meantime.
    finally:
        temporary.unlink(missing_ok=True)
