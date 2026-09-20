"""Repair a historical export whose INSERT literals were quoted twice."""
from __future__ import annotations

import argparse
from pathlib import Path


def _malformed_value(text: str, index: int) -> tuple[str, int] | None:
    if text.startswith("_binary''", index):
        cursor = index + len("_binary''")
        chars: list[str] = []
        while cursor < len(text):
            if text.startswith("''", cursor) and (cursor + 2 == len(text) or text[cursor + 2] in ',)'):
                return "_binary'" + ''.join(chars) + "'", cursor + 2
            if text[cursor] == '\\' and cursor + 1 < len(text):
                chars.extend((text[cursor], text[cursor + 1]))
                cursor += 2
                continue
            chars.append(text[cursor])
            cursor += 1
        raise ValueError('unterminated malformed binary literal')
    if not text.startswith("''", index):
        return None
    cursor = index + 2
    chars: list[str] = []
    while cursor < len(text):
        if text.startswith("''", cursor) and (cursor + 2 == len(text) or text[cursor + 2] in ',)'):
            return "'" + ''.join(chars) + "'", cursor + 2
        if text[cursor] == '\\' and cursor + 1 < len(text):
            chars.extend((text[cursor], text[cursor + 1]))
            cursor += 2
            continue
        chars.append(text[cursor])
        cursor += 1
    raise ValueError('unterminated malformed literal')


def repair_insert(line: str) -> str:
    marker = ' VALUES '
    marker_index = line.find(marker)
    if marker_index < 0:
        return line
    open_index = line.find('(', marker_index + len(marker))
    if open_index < 0 or not line.rstrip().endswith(');'):
        raise ValueError(f'unsupported INSERT shape: {line[:120]}')
    close_index = len(line.rstrip()) - 2
    body = line[open_index + 1:close_index]
    output: list[str] = []
    cursor = 0
    while cursor < len(body):
        while cursor < len(body) and body[cursor].isspace():
            output.append(body[cursor]); cursor += 1
        if cursor >= len(body):
            break
        malformed = _malformed_value(body, cursor)
        if malformed is not None:
            value, cursor = malformed
            output.append(value)
        else:
            start = cursor; quote = False; escaped = False
            while cursor < len(body):
                char = body[cursor]
                if quote:
                    if escaped: escaped = False
                    elif char == '\\': escaped = True
                    elif char == "'": quote = False
                elif char == "'": quote = True
                elif char == ',': break
                cursor += 1
            output.append(body[start:cursor])
        while cursor < len(body) and body[cursor].isspace():
            output.append(body[cursor]); cursor += 1
        if cursor < len(body):
            if body[cursor] != ',':
                raise ValueError(f'expected comma in INSERT: {line[:120]}')
            output.append(','); cursor += 1
    return line[:open_index + 1] + ''.join(output) + line[close_index:]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    # The historical writer used surrogatepass and may therefore have emitted
    # isolated non-UTF-8 bytes. Preserve them byte-for-byte while repairing the
    # ASCII SQL delimiters; the restore test remains the source of truth.
    lines = args.input.read_text(encoding='utf-8', errors='surrogateescape').splitlines(keepends=True)
    repaired = []
    count = 0
    for line in lines:
        if line.startswith('INSERT INTO '):
            ending = line[len(line.rstrip('\r\n')):]
            repaired.append(repair_insert(line.rstrip('\r\n')) + ending)
            count += 1
        else:
            repaired.append(line)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('w', encoding='utf-8', errors='surrogateescape', newline='') as stream:
        stream.write(''.join(repaired))
    print(f'repaired {count} INSERT statements')


if __name__ == '__main__':
    main()
