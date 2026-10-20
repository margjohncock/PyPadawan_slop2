"""Validate and extract small project ZIP archives."""
import re
import stat
import zipfile
from pathlib import Path, PurePosixPath


def extract_project_zip(uploaded_file, destination):
    destination = Path(destination).resolve()
    with zipfile.ZipFile(uploaded_file) as archive:
        entries = archive.infolist()
        if len(entries) > 200:
            raise ValueError('ZIP contains more than 200 entries')
        if sum(entry.file_size for entry in entries) > 10_000_000:
            raise ValueError('Uncompressed ZIP is larger than 10 MB')
        seen = set()
        for entry in entries:
            name = entry.orig_filename
            path = PurePosixPath(name)
            mode = (entry.external_attr >> 16) & 0o170000
            if (not name or name.startswith('/') or '\\' in name or ':' in name or
                    any(part in {'.', '..'} for part in name.split('/')) or
                    mode == stat.S_IFLNK or mode not in (0, stat.S_IFREG, stat.S_IFDIR)):
                raise ValueError(f'Unsafe ZIP entry: {name!r}')
            if entry.flag_bits & 1:
                raise ValueError('Encrypted ZIP entries are unsupported')
            if any(part.endswith((' ', '.')) or
                   re.fullmatch(r'(?i:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])', part.split('.')[0]) or
                   any(ord(char) < 32 or char in '<>"|?*' for char in part)
                   for part in path.parts):
                raise ValueError(f'Non-portable ZIP entry: {name!r}')
            if not destination.joinpath(*path.parts).resolve().is_relative_to(destination):
                raise ValueError(f'ZIP entry leaves extraction folder: {name!r}')
            normalized = str(path).rstrip('/').casefold()
            if normalized in seen:
                raise ValueError(f'Duplicate ZIP entry: {name!r}')
            seen.add(normalized)
        for entry in entries:
            if entry.is_dir():
                continue
            target = destination.joinpath(*PurePosixPath(entry.filename).parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(entry) as source, target.open('wb') as output:
                content = source.read(entry.file_size + 1)
                if len(content) > entry.file_size:
                    raise ValueError('ZIP entry exceeds its declared size')
                output.write(content)
