# Contributing to FastUI

Thank you for contributing to the FastUI Monorepo! To maintain code quality and engineering velocity, we adhere to standard enterprise conventions.

---

## 🌿 Git Branching Model

* **`main`**: Production-ready code. Directly deployed to production environments.
* **`dev`**: Active staging branch. All features, fixes, and improvements merge here first.
* **Feature Branches**: Named according to convention:
  * `feat/<feature-name>`
  * `fix/<bug-name>`
  * `refactor/<scope>`
  * `chore/<task>`

---

## 📝 Commit Message Conventions

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```text
<type>(<scope>): <short summary>

[optional body]
```

### Allowed Types:
* `feat`: A new user-facing or platform feature
* `fix`: A bug fix
* `refactor`: Code change that neither fixes a bug nor adds a feature
* `perf`: A code change that improves performance
* `test`: Adding missing tests or correcting existing tests
* `docs`: Documentation changes
* `chore`: Build process, tooling, or dependency updates

---

## 🧪 Pre-Commit Checklist

Before opening a pull request or pushing to `dev`:

1. **Backend Tests Pass**:
   ```bash
   cd services/api && pytest tests
   ```
2. **Frontend Typecheck & Build**:
   ```bash
   pnpm build
   ```
3. **Clean Code**: No unused imports, leftover debug `console.log` statements, or exposed secrets.
