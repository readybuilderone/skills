# Skills Repository Rules

## Bucket Structure

Skills live in `skills/{bucket}/{skill-name}/SKILL.md`.

| Bucket | Visibility | Description |
|--------|-----------|-------------|
| `engineering/` | promoted | Development, debugging, code quality |
| `productivity/` | promoted | Workflow, communication, efficiency |
| `misc/` | promoted | Everything else worth sharing |
| `deprecated/` | hidden | Legacy skills, not installed |

## Visibility Rules

- **Promoted** skills MUST appear in both top-level `README.md` AND `.claude-plugin/plugin.json`
- **Hidden** skills MUST NOT appear in either
- Each promoted bucket has its own `README.md` listing all skills in that bucket

## Adding a New Skill

1. Create `skills/{bucket}/{skill-name}/SKILL.md`
2. Add the path to `.claude-plugin/plugin.json`
3. Add a one-line entry to the top-level `README.md`
4. Add a one-line entry to the bucket's `README.md`
