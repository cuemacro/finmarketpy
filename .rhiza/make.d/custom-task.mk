## .rhiza/make.d/custom-task.mk - Custom Repository Tasks
# This file example shows how to add new targets.

.PHONY: hello-rhiza

##@ Custom Tasks
hello-rhiza: ## a custom greeting task
	@printf "${GREEN}[INFO] Hello from the customised Rhiza project!${RESET}\n"

# Adding logic to existing hooks
post-install:: ## run custom logic after core install
	@printf "${BLUE}[INFO] Running custom post-install steps...${RESET}\n"
