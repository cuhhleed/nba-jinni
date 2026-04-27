import { Component, type ErrorInfo, type ReactNode } from "react";
import { getLogger } from "../../lib/logger";

const log = getLogger("ErrorBoundary");

type Props = {
  children: ReactNode;
  fallback?: ReactNode;
};

type State = {
  hasError: boolean;
};

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false };

  static getDerivedStateFromError(): State {
    return { hasError: true };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    log.error("Component tree crashed", {
      message: error.message,
      stack: error.stack,
      componentStack: info.componentStack,
    });
  }

  render() {
    if (this.state.hasError) {
      return (
        this.props.fallback ?? (
          <div className="p-8 text-center">
            <h1 className="text-xl font-semibold mb-2">Something went wrong.</h1>
            <p className="text-gray-600">
              Try refreshing the page. If the problem persists, please report it.
            </p>
          </div>
        )
      );
    }
    return this.props.children;
  }
}