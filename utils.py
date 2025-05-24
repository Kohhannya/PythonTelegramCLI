def command(name, description=None):
    def decorator(func):
        func._command_name = name
        func._command_description = description or ""
        return func
    return decorator