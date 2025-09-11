# DataClass Configuration Fix

## Issue Description
Python 3.13 dataclass error: mutable default `<class 'list'>` for field `supported_languages` is not allowed.

## Root Cause
The `ConverterConfig` dataclass in `config.py` was using a mutable list directly as a default value, which violates Python dataclass rules.

## Solution
- Added `field` import from dataclasses
- Changed `supported_languages` from direct list assignment to `field(default_factory=lambda: ...)`

## Status
- [x] Fix dataclass mutable default issue
- [x] Test main.py functionality
- [x] Verify no regression in configuration loading

## Verification
```bash
source venv/bin/activate
python main.py --help  # Should show help without errors
```
