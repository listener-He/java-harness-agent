---
name: "global-backend-standards"
description: "The MASTER index skill for all backend development. Invoke this IMMEDIATELY when the user asks to start a new backend task, create an API, write SQL, or refactor code. It routes you to the specific standard skills."
---

# Global Backend Standards (Master Index)

**CRITICAL: You MUST read and follow this guide before generating ANY backend code (Java, Spring Boot, MyBatis, etc.).**

This project has an extremely strict set of coding, architectural, and performance standards. Failure to follow them will result in code rejection.

> **💡 NOTE ON DEVOPS PROCESS**: If you are starting a new feature from scratch, modifying an existing feature, or participating in the software development lifecycle, you MUST first consult the `devops-lifecycle-master` skill to follow the PDD, FDD, SDD, and TDD workflow.

This skill serves as an index for **Code Implementation**. Depending on the task you are performing, you **MUST** consult the corresponding sub-skills or strictly follow the rules summarized below.

## 🔗 The Skill Ecosystem (Sub-Skills)

If your task involves specific domains, you must invoke the following skills (or recall their rules if already loaded):

1. **Architecture & File Placement** -> `java-engineering-standards`
   - Covers: Controller/Service/Mapper layering, POJO package structure (`request`, `response`, `entity`, `constants`).
2. **API & Controller Design** -> `java-backend-api-standard`
   - Covers: NO Path Variables (`@PathVariable` is banned), action verbs in URLs (`/add`, `/page`), `@ResourceLock`, `@Validated`.
3**Service Logic & Utilities** -> `java-backend-guidelines`
   - Covers: In-memory data assembly strategy (Anti-JOIN), standardized pagination wrappers, `Objects` utility, `BeanUtil`.
4**Database & SQL Performance** -> `mybatis-sql-standard`
   - Covers: Anti-JOIN strategy, preventing implicit type conversion, leftmost prefix index rules, banning `SELECT *`.
5**Code Style & Formatting** -> `checkstyle`
   - Covers: K&R braces, 4-space indentation, strict Javadoc, lowerCamelCase.
6**Error Codes** -> `error-code-standard`
   - Covers: Unified error response format, domain-driven exceptions, abstract error codes.

---

## ⚡ The "Non-Negotiable" Checklist (MANDATORY CR)

Before presenting your code to the user, you **MUST** invoke the `code-review-checklist` skill or mentally execute its self-correction loop. 
If your code fails any check (e.g. you used `@PathVariable`, wildcard imports, or `SELECT *`), you MUST fix it automatically before replying.

## Commands for AI Agent
If the user uses these commands, execute the corresponding behavior based on the standards above:
- `/gen-api`: Generate Controller + Request + Response following the NO Path Variable, verb-suffix URL, and `@ResourceLock` rules.
- `/gen-service`: Generate Service Impl returning ApiResponse for writes, and using in-memory assembly / standardized pagination for reads.
- `/optimize-sql`: Review XML/LambdaQuery for JOINs, type conversions, and index order. Rewrite to application-level assembly if necessary.
- `/add-perm`: Add `@BeforePermission` to actions, or inject tenant/dept filters into `lambdaQuery`.
