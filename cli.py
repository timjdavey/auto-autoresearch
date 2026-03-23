"""CLI command builder — abstracts Claude vs Gemini CLI differences."""

# Model short-name → (cli_binary, full_model_id)
MODELS = {
    # Claude models (Claude CLI resolves short names natively)
    "opus": ("claude", "opus"),
    "sonnet": ("claude", "sonnet"),
    "haiku": ("claude", "haiku"),
    # Gemini models
    "pro": ("gemini", "gemini-2.5-pro"),
    "flash": ("gemini", "gemini-2.5-flash"),
}


def resolve_model(name):
    """Return (cli_binary, model_id) for a model name.

    Known short names are looked up in MODELS.
    Unknown names starting with 'gemini' use the gemini CLI.
    Everything else falls through to the claude CLI.
    """
    if name in MODELS:
        return MODELS[name]
    if name.startswith("gemini"):
        return ("gemini", name)
    return ("claude", name)


def build_cmd(model, prompt, allowed_tools=None):
    """Build a CLI command and determine how to pass the prompt.

    Returns (cmd_list, stdin_input):
      - Claude: prompt piped via stdin  → stdin_input = prompt
      - Gemini: prompt as -p arg       → stdin_input = None
    """
    cli, model_id = resolve_model(model)

    if cli == "gemini":
        cmd = [
            "gemini",
            "-p", prompt,
            "--model", model_id,
            "--output-format", "stream-json",
            "--yolo",
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
