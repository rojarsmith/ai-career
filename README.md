# ai-career

[繁體中文](README.zh-TW.md)

An AI-powered job application automation tool.

## Setup

Requirements: Claude Code, Python 3.11+ and Git.

### 1. Create your local config

Copy the template, then set where private data should live:

```powershell
Copy-Item config\config.example.toml config\config.toml
```

```toml
[paths]
private_data_root = 'C:\path\to\ai-career\private'
```

Use single quotes so Windows backslashes are kept as-is. `config/config.toml` is machine-specific and never committed. The repository already ignores `private/`, so a `private` folder inside the repository works as-is.

### 2. Run `/ai-career initial`

In Claude Code, from this repository:

```
/ai-career initial
```

It creates:

| Path | Purpose |
|---|---|
| `<private_data_root>\` | Root for all private data |
| `<private_data_root>\account\` | Credential files (usernames and passwords) |
| `<private_data_root>\.gitignore` | Ignores everything in the root, as a second guard |

- Safe to run repeatedly: it only creates what is missing.
- `/ai-career initial --dry-run` shows what would be created without changing anything.
- Without Claude Code, run the script directly: `python script/init_private_root.py [--dry-run]`.

**Safety checks.** If `private_data_root` is inside this repository, it must already be git-ignored; otherwise the command refuses and creates nothing, because `account\` holds passwords and this repository is public. It also refuses an empty or relative path, or the repository root itself.

The command never creates or reads credential files. Add them to `account\` yourself; they are stored unencrypted unless you encrypt them.

Exit codes: `0` success, `2` configuration or safety check failed.

Run `/ai-career help` to list all modes.
