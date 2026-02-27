# Git History Generator

This directory contains scripts to generate git commit history for the Zomato EdgeVision project.

## Overview

The scripts create a realistic commit history spanning the last 3 days with contributions from two developers:
- **Sanika-13** (sanika@example.com)
- **VitthalGund** (vitthal@example.com)

## Commit Structure

### Day 1 (3 days ago) - Project Setup
1. **Sanika-13**: Initial commit with documentation and license
2. **VitthalGund**: Add spec documents (requirements, design, tasks)
3. **Sanika-13**: Setup FastAPI backend with MongoDB
4. **VitthalGund**: Setup Next.js 14 frontend
5. **Sanika-13**: Add project documentation

### Day 2 (2 days ago) - Database and Models
6. **VitthalGund**: Implement MongoDB schemas with Pydantic
7. **VitthalGund**: Add MongoDB indexes
8. **Sanika-13**: Create demo data seeder
9. **VitthalGund**: Implement crypto service (SHA-256)
10. **Sanika-13**: Add crypto service tests

### Day 3 (1 day ago to today) - API Endpoints
11. **Sanika-13**: Add VerificationPayload model
12. **VitthalGund**: Add payload validation tests
13. **Sanika-13**: Implement verification endpoint
14. **VitthalGund**: Add endpoint integration tests
15. **Sanika-13**: Add frontend crypto utilities
16. **VitthalGund**: Update documentation

## Usage

### Linux/Mac:
```bash
chmod +x create_git_history.sh
./create_git_history.sh
```

### Windows:
```cmd
create_git_history.bat
```

## Important Notes

1. **Backup First**: If you have existing git history, back it up before running these scripts
2. **Clean State**: These scripts work best on a fresh repository
3. **Not Committed**: The scripts themselves are in .gitignore and won't be committed
4. **Email Addresses**: Update the email addresses in the scripts if needed

## What Gets Committed

The scripts commit all the work completed in Tasks 1-4.2:
- Project scaffolding (Next.js + FastAPI)
- MongoDB schemas and indexes
- Demo data seeder
- Cryptographic hash service
- Verification endpoint
- All tests and documentation

## Verification

After running the script, verify the history:

```bash
# View commit log
git log --oneline --all --graph --decorate

# View contributors
git shortlog -sn --all

# View detailed log with authors
git log --pretty=format:"%h - %an, %ar : %s"
```

Expected output:
- 16 commits total
- 8 commits by Sanika-13
- 8 commits by VitthalGund
- Commits spread over 3 days

## Troubleshooting

### "fatal: not a git repository"
Run `git init` first, then run the script again.

### Commits not showing correct dates
The scripts use relative dates ("3 days ago", "2 days ago", etc.) which should work on most systems. If dates are incorrect, you may need to adjust the date format in the script for your system.

### Permission denied (Linux/Mac)
Make the script executable: `chmod +x create_git_history.sh`

## Customization

To customize the commit history:
1. Edit the script file
2. Modify commit messages, dates, or authors
3. Add or remove commits as needed
4. Run the script

## Clean Up

To remove the generated history and start fresh:
```bash
rm -rf .git
git init
```

Then run the script again.
