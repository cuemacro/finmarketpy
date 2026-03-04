## github.mk - github repo maintenance and helpers
# This file is included by the main Makefile

# ── Forge Detection ──────────────────────────────────────────────────────────
# FORGE_TYPE is set once and reused by any target that needs to know the forge.
# Priority: .github/workflows/ → .gitlab-ci.yml / .gitlab/ → unknown
FORGE_TYPE := $(if $(wildcard .github/workflows/),github,$(if $(or $(wildcard .gitlab-ci.yml),$(wildcard .gitlab/)),gitlab,unknown))

# Declare phony targets
.PHONY: gh-install require-gh view-prs view-issues failed-workflows workflow-status latest-release whoami print-logo

# ── Internal guard ───────────────────────────────────────────────────────────
# Require the gh CLI; hard-fail if missing so downstream targets can depend on it.
require-gh:
	@if ! command -v gh >/dev/null 2>&1; then \
		printf "${RED}[ERROR] gh cli not found. Install from: https://github.com/cli/cli?tab=readme-ov-file#installation${RESET}\n"; \
		exit 1; \
	fi

##@ GitHub Helpers
gh-install: ## check for gh cli existence and install extensions
	@if ! command -v gh >/dev/null 2>&1; then \
		printf "${YELLOW}[WARN] gh cli not found.${RESET}\n"; \
		printf "${BLUE}[INFO] Please install it from: https://github.com/cli/cli?tab=readme-ov-file#installation${RESET}\n"; \
	else \
		printf "${GREEN}[INFO] gh cli is installed.${RESET}\n"; \
	fi

view-prs: gh-install ## list open pull requests
	@printf "${BLUE}[INFO] Open Pull Requests:${RESET}\n"
	@gh pr list --json number,title,author,headRefName,updatedAt --template \
		'{{tablerow (printf "NUM" | color "bold") (printf "TITLE" | color "bold") (printf "AUTHOR" | color "bold") (printf "BRANCH" | color "bold") (printf "UPDATED" | color "bold")}}{{range .}}{{tablerow (printf "#%v" .number | color "green") .title (.author.login | color "cyan") (.headRefName | color "yellow") (timeago .updatedAt | color "white")}}{{end}}'

view-issues: gh-install ## list open issues
	@printf "${BLUE}[INFO] Open Issues:${RESET}\n"
	@gh issue list --json number,title,author,labels,updatedAt --template \
		'{{tablerow (printf "NUM" | color "bold") (printf "TITLE" | color "bold") (printf "AUTHOR" | color "bold") (printf "LABELS" | color "bold") (printf "UPDATED" | color "bold")}}{{range .}}{{tablerow (printf "#%v" .number | color "green") .title (.author.login | color "cyan") (pluck "name" .labels | join ", " | color "yellow") (timeago .updatedAt | color "white")}}{{end}}'

failed-workflows: gh-install ## list recent failing workflow runs
	@printf "${BLUE}[INFO] Recent Failing Workflow Runs:${RESET}\n"
	@gh run list --limit 10 --status failure --json conclusion,name,headBranch,event,createdAt --template \
		'{{tablerow (printf "STATUS" | color "bold") (printf "NAME" | color "bold") (printf "BRANCH" | color "bold") (printf "EVENT" | color "bold") (printf "TIME" | color "bold")}}{{range .}}{{tablerow (printf "%s" .conclusion | color "red") .name (.headBranch | color "cyan") (.event | color "yellow") (timeago .createdAt | color "white")}}{{end}}'

whoami: gh-install ## check github auth status
	@printf "${BLUE}[INFO] GitHub Authentication Status:${RESET}\n"
	@gh auth status --hostname github.com --json hosts --template \
		'{{range $$host, $$accounts := .hosts}}{{range $$accounts}}{{if .active}}  {{printf "✓" | color "green"}} Logged in to {{$$host}} account {{.login | color "bold"}} ({{.tokenSource}}){{"\n"}}  Active account: {{printf "true" | color "green"}}{{"\n"}}  Git operations protocol: {{.gitProtocol | color "yellow"}}{{"\n"}}  Token scopes: {{.scopes | color "yellow"}}{{"\n"}}{{end}}{{end}}{{end}}'

workflow-status: require-gh ## show recent runs for the release workflow
	@printf "${BOLD}Release Workflow Status${RESET}\n"
	@printf "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}\n"
	@RELEASE_WF=$$(gh workflow list --json name,id --jq '.[] | select(.name | test("release";"i")) | .name' 2>/dev/null | head -1); \
	if [ -n "$$RELEASE_WF" ]; then \
		printf "${BLUE}[INFO] Workflow: ${GREEN}$$RELEASE_WF${RESET}\n\n"; \
		gh run list --workflow "$$RELEASE_WF" --limit 5 \
			--json status,conclusion,headBranch,event,createdAt,displayTitle,url \
			--template '{{tablerow (printf "STATUS" | color "bold") (printf "CONCLUSION" | color "bold") (printf "TITLE" | color "bold") (printf "EVENT" | color "bold") (printf "TIME" | color "bold")}}{{range .}}{{tablerow (printf "%s" .status | color "cyan") (printf "%s" (or .conclusion "—") | color (or (and (eq .conclusion "success") "green") (and (eq .conclusion "failure") "red") "yellow")) .displayTitle (.event | color "yellow") (timeago .createdAt | color "white")}}{{end}}'; \
	else \
		printf "${YELLOW}[WARN] No release workflow found in this repository${RESET}\n"; \
	fi

latest-release: require-gh ## show information about the latest GitHub release
	@printf "${BOLD}Latest Release${RESET}\n"
	@printf "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}\n"
	@if gh release view --json tagName --jq '.tagName' >/dev/null 2>&1; then \
		gh release view --json tagName,name,publishedAt,url,isDraft,isPrerelease,author \
			--template '  Tag:          {{.tagName | color "green"}}{{"\n"}}  Name:         {{.name}}{{"\n"}}  Author:       {{.author.login}}{{"\n"}}  Published:    {{timeago .publishedAt}}{{"\n"}}  Status:       {{if .isDraft}}{{printf "Draft" | color "yellow"}}{{else if .isPrerelease}}{{printf "Pre-release" | color "yellow"}}{{else}}{{printf "Published" | color "green"}}{{end}}{{"\n"}}  URL:          {{.url}}{{"\n"}}'; \
	else \
		printf "${YELLOW}[WARN] No releases found in this repository${RESET}\n"; \
	fi
