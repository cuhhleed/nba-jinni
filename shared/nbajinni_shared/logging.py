import structlog


def configure_logging():
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S", utc=True),
        structlog.processors.JSONRenderer()
    ]

    structlog.configure(processors=processors)

def get_logger(component):
    return structlog.get_logger(component=component)
