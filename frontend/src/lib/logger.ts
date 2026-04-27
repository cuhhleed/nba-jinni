type LogContext = Record<string, unknown>;

const isDev = import.meta.env.DEV;

function format(component: string, message: string, context?: LogContext) {
  return context ? [`[${component}] ${message}`, context] : [`[${component}] ${message}`];
}

export function getLogger(component: string) {
  return {
    debug: (message: string, context?: LogContext) => {
      if (isDev) console.debug(...format(component, message, context));
    },
    info: (message: string, context?: LogContext) => {
      if (isDev) console.info(...format(component, message, context));
    },
    warn: (message: string, context?: LogContext) => {
      console.warn(...format(component, message, context));
    },
    error: (message: string, context?: LogContext) => {
      console.error(...format(component, message, context));
    },
  };
}

export type Logger = ReturnType<typeof getLogger>;
