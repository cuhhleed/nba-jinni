import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { isAxiosError } from "axios";
import { BrowserRouter, Route, Routes } from "react-router";
import Navbar from "./components/layout/Navbar";
import { ErrorBoundary } from "./components/ui/ErrorBoundary";
import GameDetail from "./routes/GameDetail";
import Home from "./routes/Home";
import PlayerDetail from "./routes/PlayerDetail";
import SearchResults from "./routes/SearchResults";
import Standings from "./routes/Standings";
import TeamDetail from "./routes/TeamDetail";
import Teams from "./routes/Teams";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: (failureCount, error) => {
        if (
          isAxiosError(error) &&
          error.response &&
          error.response.status >= 400 &&
          error.response.status < 500
        ) {
          return false;
        }
        return failureCount < 3;
      },
    },
  },
});

function App() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <Navbar />
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/teams" element={<Teams />} />
            <Route path="/teams/:id" element={<TeamDetail />} />
            <Route path="/players/:id" element={<PlayerDetail />} />
            <Route path="/search" element={<SearchResults />} />
            <Route path="/standings" element={<Standings />} />
            <Route path="/games/:id" element={<GameDetail />} />
          </Routes>
        </BrowserRouter>
      </QueryClientProvider>
    </ErrorBoundary>
  );
}

export default App;
