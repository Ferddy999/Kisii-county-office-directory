# Working together

Everyone works on their own branch. Nobody pushes straight to `main`.

## Every change, step by step

1. Pick or create an issue on GitHub for the task and assign it to yourself.
2. Make sure you start from the latest code:

   ```powershell
   git checkout main
   git pull
   ```

3. Create a branch named for the work:

   ```powershell
   git checkout -b feature/short-description
   ```

   Use `feature/` for new work, `fix/` for bug fixes and `docs/` for documentation.

4. Make your changes in small steps and commit often:

   ```powershell
   git add -A
   git commit -m "Add filter by directorate to office list"
   ```

   Write commit messages in the present tense, saying what the change does.

5. Run the tests and the checks:

   ```powershell
   python manage.py test
   python manage.py check
   ```

6. Push your branch and open a pull request on GitHub:

   ```powershell
   git push -u origin feature/short-description
   ```

7. Ask a teammate to review it. Fix what they raise. When it is approved and the tests pass, merge it, then update your own copy:

   ```powershell
   git checkout main
   git pull
   ```

## Rules

- Do not commit `.env`, passwords, keys or real county data.
- Add or update tests for any change to permissions, validation or sign-in.
- Keep pull requests small and about one thing.
- Do not merge your own pull request without a review.
- If two people need the same file, tell each other first and merge often to avoid conflicts.
- Use your own name and email in Git so your work is credited to you:

  ```powershell
  git config user.name "Your Name"
  git config user.email "you@example.com"
  ```

## Code style

- Python: follow PEP 8, keep views short, and put checks in forms and models rather than in templates.
- Templates: reuse the partials in `templates/partials/`. Use the colours and spacing variables in `static/css/site.css` instead of new hard-coded values.
- Every page must work with a keyboard, have labelled form fields, and stay usable on a phone.

## Weekly review

Before each weekly review, make sure your pull requests are open or merged and your issues are updated, so progress is visible on GitHub.
