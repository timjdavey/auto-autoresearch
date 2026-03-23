"""CLI command builder — abstracts Claude vs Codex CLI differences."""

# Model short-name → (cli_binary, full_model_id)
MODELS = {
    # Claude models (Claude CLI resolves short names natively)
    "opus": ("claude", "opus"),
    "sonnet": ("claude", "sonnet"),
    "haiku": ("claude", "haiku"),
    # Codex models
    "codex": ("codex", "gpt-5.4-mini"),
    "codex-mini": ("codex", "gpt-5.4-mini"),
    "codex-full": ("codex", "gpt-5.4"),
}


def resolve_model(name):
    """Return (cli_binary, model_id) for a model name.

    Known short names are looked up in MODELS.
    Unknown names starting with 'gpt' use the codex CLI.
    Everything else falls through to the claude CLI.
    """
    if name in MODELS:
        return MODELS[name]
    if name.startswith("gpt"):
        return ("codex", name)
    return ("claude", name)


def build_cmd(model, prompt, allowed_tools=None):
    """Build a CLI command and determine how to pass the prompt.

    Returns (cmd_list, stdin_input):
      - Claude: prompt piped via stdin  → stdin_input = prompt
      - Codex:  prompt as positional arg → stdin_input = None
    """
    cli, model_id = resolve_model(model)

    if cli == "codex":
        cmd = [
            "codex", "exec", prompt,
            "--model", model_id,
            "--json",
            "--full-auto",
        ]
        return cmd, None
    else:
        cmd = [
            "claude", "-p",
            "--verbose",
            "--model", model_id,
            "--output-format", "stream-json",
        ]
        if allowed_tools:
            cmd += ["--allowedTools", allowed_tools]
        return cmd, prompt
